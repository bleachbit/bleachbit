# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2021 Andrew Ziem
# https://www.bleachbit.org
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from bleachbit.FileUtilities import extended_path, extended_path_undo
"""
***
*** Owner: Andrew Ziem
*** Author: Peter Marshall
***
*** References:
*** Windows Internals (Russinovich, Solomon, Ionescu), 6th edition
*** http://windowsitpro.com/systems-management/inside-windows-nt-disk-defragmenting
*** https://technet.microsoft.com/en-us/sysinternals/sdelete.aspx
*** https://blogs.msdn.microsoft.com/jeffrey_wall/2004/09/13/defrag-api-c-wrappers/
*** https://msdn.microsoft.com/en-us/library/windows/desktop/aa364572(v=vs.85).aspx
***
***
*** Algorithm
***   --Phase 1
*** - Check if the file has special characteristics (sparse, encrypted,
***   compressed), determine file system (NTFS or FAT), Windows version.
*** - Read the on-disk locations of the file using defrag API.
*** - If file characteristics don't rule it out, just do a direct write
***   of zero-fill on entire file size and flush to disk.
*** - Read back the on-disk locations of the file using defrag API.
*** - If locations are exactly the same, we are done.
*** - Otherwise, enumerate clusters that did not get overwritten in place
***   ("missed clusters").
***   They are probably still untouched, we need to wipe them.
*** - If it was a special file that wouldn't be wiped by a direct write,
***   we will truncate the file and treat it all as missed clusters.
***
***   --Phase 2
*** - (*) Get volume bitmap of free/allocated clusters using defrag API. 
***   Figure out if checkpoint has made our missed clusters available
***   for use again (this is potentially delayed by a few seconds in NTFS).
*** - If they have not yet been made available, wait 0.1s then repeat
***   previous check (*), up to a limit of 7s in polling.
*** - Figure out if it is better to bridge the extents, wiping more clusters
***   but gaining a performance boost from reduced total cycles and overhead.
*** - Recurse over the extents we need to wipe, breaking them down into
***   smaller extents if necessary.
*** - Write a zero-fill file that will provide enough clusters to
***   completely overwrite each extent in turn.
*** - Iterate over the zero-fill file, moving clusters from our zero file
***   to the missed clusters using defrag API.
*** - If the defrag move operation did not succeed, it was probably because
***   another process has grabbed a cluster on disk that we wanted to
***   write to. This can also happen when, by chance, the move's source and
***   target ranges overlap.
*** - In response, we can break the extent down into sub-sections and
***   attempt to wipe each subsection (eventually down to a granularity
***   of one cluster). We also inspect allocated/free sectors to look ahead
***   and avoid making move calls that we know will fail.
*** - If a cluster was allocated by some other Windows process before we could
***   explicitly wipe it, it is assumed to be wiped. Even if Windows writes a
***   small amount of explicit data to a cluster, it seems to write zero-fill
***   out to the end of the cluster to round it out.
***
***
***   TO DO
***   - Test working correctly if per-user disk quotas are in place
***
"""


# Imports.
import sys
import os
import struct
import logging
from operator import itemgetter
from random import randint
from collections import namedtuple

from win32api import (GetVolumeInformation, GetDiskFreeSpace,
                      GetVersionEx, Sleep)
from win32file import (CreateFile, CreateFileW,
                       CloseHandle, GetDriveType,
                       GetFileSize, GetFileAttributesW,
                       SetFileAttributesW,
                       DeviceIoControl, SetFilePointer,
                       WriteFile,
                       LockFile, DeleteFile,
                       SetEndOfFile, FlushFileBuffers)
from winioctlcon import (FSCTL_GET_RETRIEVAL_POINTERS,
                         FSCTL_GET_VOLUME_BITMAP,
                         FSCTL_GET_NTFS_VOLUME_DATA,
                         FSCTL_MOVE_FILE,
                         FSCTL_SET_COMPRESSION,
                         FSCTL_SET_SPARSE,
                         FSCTL_SET_ZERO_DATA)
from win32file import (GENERIC_READ, GENERIC_WRITE, FILE_BEGIN,
                       FILE_SHARE_READ, FILE_SHARE_WRITE,
                       OPEN_EXISTING, CREATE_ALWAYS, FILE_FLAG_BACKUP_SEMANTICS,
                       DRIVE_REMOTE, DRIVE_CDROM, DRIVE_UNKNOWN)
from win32con import (FILE_ATTRIBUTE_ENCRYPTED,
                      FILE_ATTRIBUTE_COMPRESSED,
                      FILE_ATTRIBUTE_SPARSE_FILE,
                      FILE_ATTRIBUTE_HIDDEN,
                      FILE_ATTRIBUTE_READONLY,
                      FILE_FLAG_RANDOM_ACCESS,
                      FILE_FLAG_NO_BUFFERING,
                      FILE_FLAG_WRITE_THROUGH,
                      COMPRESSION_FORMAT_DEFAULT)
VER_SUITE_PERSONAL = 0x200   # doesn't seem to be present in win32con.


# Constants.
simulate_concurrency = False     # remove this test function when QA complete
# drive_letter_safety = "E"       # protection to only use removeable drives
# don't use C: or D:, but E: and beyond OK.
tmp_file_name = "bbtemp.dat"
spike_file_name = "bbspike"     # cluster number will be appended
write_buf_size = 512 * 1024     # 512 kilobytes

# Set up logging
logger = logging.getLogger(__name__)

# Unpacks the next element in a structure, using format requested.
# Returns the element and the remaining content of the structure.


def unpack_element(fmt, structure):
    chunk_size = struct.calcsize(fmt)
    element = struct.unpack(fmt, structure[:chunk_size])
    if element and len(element) > 0:
        element = element[0]    # convert from tuple to single element
    structure = structure[chunk_size:]
    return element, structure


# GET_RETRIEVAL_POINTERS gives us a list of VCN, LCN tuples.
# Convert from that format into a list of cluster start/end tuples.
# The flag for writing bridged extents is a way of handling
# the structure of compressed files. If a part of the file is close
# to contiguous on disk, bridge its extents to combine them, even
# though there are some unrelated clusters in between.
# Generator function, will return results one tuple at a time.
def logical_ranges_to_extents(ranges, bridge_compressed=False):
    if not bridge_compressed:
        vcn_count = 0
        for vcn, lcn in ranges:
            # If we encounter an LCN of -1, we have reached a
            # "space-saved" part of a compressed file. These clusters
            # don't map to clusters on disk, just advance beyond them.
            if lcn < 0:
                vcn_count = vcn
                continue

            # Figure out length for this cluster range.
            # Keep track of VCN inside this file.
            this_vcn_span = vcn - vcn_count
            vcn_count = vcn
            assert this_vcn_span >= 0

            yield (lcn, lcn + this_vcn_span - 1)

    else:
        vcn_count = 0
        last_record = len(ranges)
        index = 0
        while index < last_record:
            vcn, lcn = ranges[index]

            # If we encounter an LCN of -1, we have reached a
            # "space-saved" part of a compressed file. These clusters
            # don't map to clusters on disk, just advance beyond them.
            if lcn < 0:
                vcn_count = vcn
                index += 1
                continue

            # Figure out if we have a block of clusters that can
            # be merged together. The pattern is regular disk
            # clusters interspersed with -1 space-saver sections
            # that are arranged with gaps of 16 clusters or less.
            merge_index = index
            while (lcn >= 0 and
                   merge_index + 2 < last_record and
                   ranges[merge_index + 1][1] < 0 and
                   ranges[merge_index + 2][1] >= 0 and
                   ranges[merge_index + 2][1] - ranges[merge_index][1] <= 16 and
                   ranges[merge_index + 2][1] - ranges[merge_index][1] > 0):
                merge_index += 2

            # Figure out length for this cluster range.
            # Keep track of VCN inside this file.
            if merge_index == index:
                index += 1
                this_vcn_span = vcn - vcn_count
                vcn_count = vcn
                assert this_vcn_span >= 0
                yield (lcn, lcn + this_vcn_span - 1)
            else:
                index = merge_index + 1
                last_vcn_span = (ranges[merge_index][0] -
                                 ranges[merge_index - 1][0])
                vcn = ranges[merge_index][0]
                vcn_count = vcn
                assert last_vcn_span >= 0
                yield (lcn, ranges[merge_index][1] + last_vcn_span - 1)


# Determine clusters that are in extents list A but not in B.
# Generator function, will return results one tuple at a time.
def extents_a_minus_b(a, b):
    # Sort the lists of start/end points.
    a_sorted = sorted(a, key=itemgetter(0))
    b_sorted = sorted(b, key=itemgetter(0))
    b_is_empty = not b

    for a_begin, a_end in a_sorted:
        # If B is an empty list, each item of A will be unchanged.
        if b_is_empty:
            yield (a_begin, a_end)

        for b_begin, b_end in b_sorted:
            if b_begin > a_end:
                # Already gone beyond current A range and no matches.
                # Return this range of A unbroken.
                yield (a_begin, a_end)
                break
            elif b_end < a_begin:
                # Too early in list, keep searching.
                continue
            elif b_begin <= a_begin:
                if b_end >= a_end:
                    # This range of A is completely covered by B.
                    # Do nothing and pass on to next range of A.
                    break
                else:
                    # This range of A is partially covered by B.
                    # Remove the covered range from A and loop
                    a_begin = b_end + 1
            else:
                # This range of A is partially covered by B.
                # Return the first part of A not covered.
                # Either process remainder of A range or move to next A.
                yield (a_begin, b_begin - 1)
                if b_end >= a_end:
                    break
                else:
                    a_begin = b_end + 1


# Decide if it will be more efficient to bridge the extents and wipe
# some additional clusters that weren't strictly part of the file.
# By grouping write/move cycles into larger portions, we can reduce
# overhead and complete the wipe quicker - even though it involves
# a higher number of total clusters written.
def choose_if_bridged(volume_handle, total_clusters,
                      orig_extents, bridged_extents):
    logger.debug('bridged extents: {}'.format(bridged_extents))
    allocated_extents = []
    volume_bitmap, bitmap_size = get_volume_bitmap(volume_handle,
                                                   total_clusters)
    count_ofree, count_oallocated = check_extents(
        orig_extents, volume_bitmap)
    count_bfree, count_ballocated = check_extents(
        bridged_extents,
        volume_bitmap,
        allocated_extents)
    bridged_extents = [x for x in extents_a_minus_b(bridged_extents,
                                                    allocated_extents)]

    extra_allocated_clusters = count_ballocated - count_oallocated
    saving_in_extents = len(orig_extents) - len(bridged_extents)
    logger.debug(("Bridged extents would require us to work around %d " +
                  "more allocated clusters.") % extra_allocated_clusters)
    logger.debug("It would reduce extent count from %d to %d." % (
        len(orig_extents), len(bridged_extents)))

    # Use a penalty of 10 extents for each extra allocated cluster.
    # Why 10? Assuming our next granularity above 1 cluster is a 10 cluster
    # extent, a single allocated cluster would cause us to perform 8
    # additional write/move cycles due to splitting that extent into single
    # clusters.
    # If we had a notion of distribution of extra allocated clusters,
    # we could make this calc more exact. But it's just a rule of thumb.
    tradeoff = saving_in_extents - extra_allocated_clusters * 10
    if tradeoff > 0:
        logger.debug("Quickest method should be bridged extents")
        return bridged_extents
    else:
        logger.debug("Quickest method should be original extents")
        return orig_extents


# Break an extent into smaller portions (numbers are tuned to give something
# in the range of 8 to 15 portions).
# Generator function, will return results one tuple at a time.
def split_extent(lcn_start, lcn_end):
    split_factor = 10

    exponent = 0
    count = lcn_end - lcn_start + 1
    while count > split_factor**(exponent + 1.3):
        exponent += 1
    extent_size = split_factor**exponent
    for x in range(lcn_start, lcn_end + 1, extent_size):
        yield (x, min(x + extent_size - 1, lcn_end))


# Check extents to see if they are marked as free.
def check_extents(extents, volume_bitmap, allocated_extents=None):
    count_free, count_allocated = (0, 0)
    for lcn_start, lcn_end in extents:
        for cluster in range(lcn_start, lcn_end + 1):
            if check_mapped_bit(volume_bitmap, cluster):
                count_allocated += 1
                if allocated_extents is not None:
                    allocated_extents.append((cluster, cluster)) # Modified by Marvin [12/05/2020] The extents should have (start, end) format 
            else:
                count_free += 1

    logger.debug("Extents checked: clusters free %d; allocated %d",
                 count_free, count_allocated)
    return (count_free, count_allocated)


# Check extents to see if they are marked as free.
# Copy of the above that simulates concurrency for testing purposes.
# Once every x clusters at random it will allocate a cluster on disk
# to prove that the algorithm can handle it.
def check_extents_concurrency(extents, volume_bitmap,
                              tmp_file_path, volume_handle,
                              total_clusters,
                              allocated_extents=None):
    odds_to_allocate = 1200    # 1 in 1200

    count_free, count_allocated = (0, 0)
    for lcn_start, lcn_end in extents:
        for cluster in range(lcn_start, lcn_end + 1):
            # Every once in a while, occupy a particular cluster on disk.
            if randint(1, odds_to_allocate) == odds_to_allocate:
                spike_cluster(volume_handle, cluster, tmp_file_path)
                if bool(randint(0, 1)):
                    # Simulate allocated before the check, by refetching
                    # the volume bitmap.
                    logger.debug("Simulate known allocated")
                    volume_bitmap, _ = get_volume_bitmap(
                        volume_handle, total_clusters)
                else:
                    # Simulate allocated after the check.
                    logger.debug("Simulate unknown allocated")

            if check_mapped_bit(volume_bitmap, cluster):
                count_allocated += 1
                if allocated_extents is not None:
                    allocated_extents.append(cluster)
            else:
                count_free += 1

    logger.debug("Extents checked: clusters free %d; allocated %d",
                 count_free, count_allocated)
    return (count_free, count_allocated)


# Allocate a cluster on disk by pinning it with a file.
# This simulates another process having grabbed it while our
# algorithm is working.
# This is only used for testing, especially testing concurrency issues.
def spike_cluster(volume_handle, cluster, tmp_file_path):
    spike_file_path = os.path.dirname(tmp_file_path)
    if spike_file_path[-1] != os.sep:
        spike_file_path += os.sep
    spike_file_path += spike_file_name + str(cluster)
    file_handle = CreateFile(spike_file_path,
                             GENERIC_READ | GENERIC_WRITE,
                             FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                             None, CREATE_ALWAYS, 0, None)
    # 2000 bytes is enough to direct the file to its own cluster and not
    # land entirely in the MFT.
    write_zero_fill(file_handle, 2000)
    move_file(volume_handle, file_handle, 0, cluster, 1)
    CloseHandle(file_handle)
    logger.debug("Spiked cluster %d with %s" % (cluster, spike_file_path))


# Check if an LCN is allocated (True) or free (False).
# The LCN determines at what index into the bytes/bits structure we
# should look.
def check_mapped_bit(volume_bitmap, lcn):
    assert isinstance(lcn, int)
    mapped_bit = volume_bitmap[lcn // 8]
    bit_location = lcn % 8    # zero-based
    if bit_location > 0:
        mapped_bit = mapped_bit >> bit_location
    mapped_bit = mapped_bit & 1
    return mapped_bit > 0


# Check the operating system. Go no further unless we are on
# Windows and it's Win NT or later.
def check_os():
    if os.name.lower() != "nt":
        raise RuntimeError("This function requires Windows NT or later")


# Determine which version of Windows we are running.
# Not currently used, except to control encryption test case
# depending on whether it's Windows Home Edition or something higher end.
def determine_win_version():
    ver_info = GetVersionEx(1)
    is_home = bool(ver_info[7] & VER_SUITE_PERSONAL)
    if ver_info[:2] == (6, 0):
        return "Vista", is_home
    elif ver_info[0] >= 6:
        return "Later than Vista", is_home
    else:
        return "Something else", is_home


# Open the file to get a Windows file handle, ensuring it exists.
# CreateFileW gives us Unicode support.
def open_file(file_name, mode=GENERIC_READ):
    file_handle = CreateFileW(file_name, mode, 0, None,
                              OPEN_EXISTING, FILE_FLAG_BACKUP_SEMANTICS, None)
    return file_handle


# Close file
def close_file(file_handle):
    CloseHandle(file_handle)


# Get some basic information about a file.
def get_file_basic_info(file_name, file_handle):
    file_attributes = GetFileAttributesW(file_name)
    file_size = GetFileSize(file_handle)
    is_compressed = bool(file_attributes & FILE_ATTRIBUTE_COMPRESSED)
    is_encrypted = bool(file_attributes & FILE_ATTRIBUTE_ENCRYPTED)
    is_sparse = bool(file_attributes & FILE_ATTRIBUTE_SPARSE_FILE)
    is_special = is_compressed | is_encrypted | is_sparse
    if is_special:
        logger.debug('{}: {} {} {}'.format(file_name,
                                           'compressed' if is_compressed else '',
                                           'encrypted' if is_encrypted else '',
                                           'sparse' if is_sparse else ''))
    return file_size, is_special


# Truncate a file. Do this when we want to release its clusters.
def truncate_file(file_handle):
    SetFilePointer(file_handle, 0, FILE_BEGIN)
    SetEndOfFile(file_handle)
    FlushFileBuffers(file_handle)


# Given a Windows file path, determine the volume that contains it.
# Append the separator \ to it (more useful for subsequent calls).
def volume_from_file(file_name):
    # strip \\?\
    split_path = os.path.splitdrive(extended_path_undo(file_name))
    volume = split_path[0]
    if volume and volume[-1] != os.sep:
        volume += os.sep
    return volume


class UnsupportedFileSystemError(Exception):
    """An exception for an unsupported file system"""

# Given a volume, get the relevant volume information.
# We are interested in:
# First call: Drive Name; Max Path; File System.
# Second call: Sectors per Cluster; Bytes per Sector; Total # of Clusters.
# Third call: Drive Type.


def get_volume_information(volume):
    # If it's a UNC path, raise an error.
    if not volume:
        raise UnsupportedFileSystemError(
            "Only files with a Local File System path can be wiped.")

    result1 = GetVolumeInformation(volume)
    result2 = GetDiskFreeSpace(volume)
    result3 = GetDriveType(volume)

    for drive_enum, error_reason in [
            (DRIVE_REMOTE, "a network drive"),
            (DRIVE_CDROM, "a CD-ROM"),
            (DRIVE_UNKNOWN, "an unknown drive type")]:
        if result3 == drive_enum:
            raise UnsupportedFileSystemError(
                "This file is on %s and can't be wiped." % error_reason)

    # Only NTFS and FAT variations are supported.
    # UDF (file system for CD-RW etc) is not supported.
    if result1[4].upper() == "UDF":
        raise UnsupportedFileSystemError(
            "This file system (UDF) is not supported.")

    volume_info = namedtuple('VolumeInfo', [
        'drive_name', 'max_path', 'file_system',
        'sectors_per_cluster', 'bytes_per_sector', 'total_clusters'])

    return volume_info(result1[0], result1[2], result1[4],
                       result2[0], result2[1], result2[3])


# Get read/write access to a volume.
def obtain_readwrite(volume):
    # Optional protection that we are running on removable media only.
    assert volume
    # if drive_letter_safety:
    #    drive_containing_file = volume[0].upper()
    #    assert drive_containing_file >= drive_letter_safety.upper()

    volume = '\\\\.\\' + volume
    if volume[-1] == os.sep:
        volume = volume.rstrip(os.sep)

    # We need the FILE_SHARE flags so that this open call can succeed
    # despite something on the volume being in use by another process.
    volume_handle = CreateFile(volume, GENERIC_READ | GENERIC_WRITE,
                               FILE_SHARE_READ | FILE_SHARE_WRITE,
                               None, OPEN_EXISTING,
                               FILE_FLAG_RANDOM_ACCESS |
                               FILE_FLAG_NO_BUFFERING |
                               FILE_FLAG_WRITE_THROUGH,
                               None)
    #logger.debug("Opened volume %s", volume)

    return volume_handle


# Retrieve a list of pointers to the file location on disk.
# If translate_to_extents is False, return the Windows VCN/LCN format.
# If True, do an extra conversion to get a list of extents on disk.
def get_extents(file_handle, translate_to_extents=True):
    # Assemble input structure and query Windows for retrieval pointers.
    # The input structure is the number 0 as a signed 64 bit integer.
    input_struct = struct.pack('q', 0)
    # 4K, 32K, 256K, 2M step ups in buffer size, until call succeeds.
    # Compressed/encrypted/sparse files tend to have more chopped up extents.
    buf_retry_sizes = [4 * 1024, 32 * 1024, 256 * 1024, 2 * 1024**2]
    for retrieval_pointers_buf_size in buf_retry_sizes:
        try:
            rp_struct = DeviceIoControl(file_handle,
                                        FSCTL_GET_RETRIEVAL_POINTERS,
                                        input_struct,
                                        retrieval_pointers_buf_size)
        except:
            err_info = sys.exc_info()[1]
            err_code = err_info.winerror
            if err_code == 38:     # when file size is 0.
                # (38, 'DeviceIoControl', 'Reached the end of the file.')
                return []
            elif err_code in [122, 234]:  # when buffer not large enough.
                # (122, 'DeviceIoControl',
                # 'The data area passed to a system call is too small.')
                # (234, 'DeviceIoControl', 'More data is available.')
                pass
            else:
                raise
        else:
            # Call succeeded, break out from for loop.
            break

    # At this point we have a FSCTL_GET_RETRIEVAL_POINTERS (rp) structure.
    # Process content of the first part of structure.
    # Separate the retrieval pointers list up front, so we are not making
    # too many string copies of it.
    chunk_size = struct.calcsize('IIq')
    rp_list = rp_struct[chunk_size:]
    rp_struct = rp_struct[:chunk_size]
    record_count, rp_struct = unpack_element('I', rp_struct)    # 4 bytes
    _, rp_struct = unpack_element('I', rp_struct)               # 4 bytes
    starting_vcn, rp_struct = unpack_element('q', rp_struct)    # 8 bytes
    # 4 empty bytes were consumed above.
    # This is for reasons of 64-bit alignment inside structure.

    # If we make the GET_RETRIEVAL_POINTERS request with 0,
    # this should always come back 0.
    assert starting_vcn == 0

    # Populate the extents array with the ranges from rp structure.
    ranges = []
    c = record_count
    i = 0
    chunk_size = struct.calcsize('q')
    buf_size = len(rp_list)
    while c > 0 and i < buf_size:
        next_vcn = struct.unpack_from('q', rp_list, offset=i)
        lcn = struct.unpack_from('q', rp_list, offset=i + chunk_size)
        ranges.append((next_vcn[0], lcn[0]))
        i += chunk_size * 2
        c -= 1

    if not translate_to_extents:
        return ranges
    else:
        return [x for x in logical_ranges_to_extents(ranges)]


# Tell Windows to make this file compressed on disk.
# Only used for the test suite.
def file_make_compressed(file_handle):
    # Assemble input structure.
    # Just tell Windows to use standard compression.
    input_struct = struct.pack('H', COMPRESSION_FORMAT_DEFAULT)
    buf_size = struct.calcsize('H')

    _ = DeviceIoControl(file_handle, FSCTL_SET_COMPRESSION,
                        input_struct, buf_size)


# Tell Windows to make this file sparse on disk.
# Only used for the test suite.
def file_make_sparse(file_handle):
    _ = DeviceIoControl(file_handle, FSCTL_SET_SPARSE, None, None)


# Tell Windows to add a zero region to a sparse file.
# Only used for the test suite.
def file_add_sparse_region(file_handle, byte_start, byte_end):
    # Assemble input structure.
    input_struct = struct.pack('qq', byte_start, byte_end)
    buf_size = struct.calcsize('qq')

    _ = DeviceIoControl(file_handle, FSCTL_SET_ZERO_DATA,
                        input_struct, buf_size)


# Retrieve a bitmap of whether clusters on disk are free/allocated.
def get_volume_bitmap(volume_handle, total_clusters):
    # Assemble input structure and query Windows for volume bitmap.
    # The input structure is the number 0 as a signed 64 bit integer.
    input_struct = struct.pack('q', 0)

    # Figure out the buffer size. Add small fudge factor to ensure success.
    buf_size = int(total_clusters / 8) + 16 + 64

    vb_struct = DeviceIoControl(volume_handle, FSCTL_GET_VOLUME_BITMAP,
                                input_struct, buf_size)

    # At this point we have a FSCTL_GET_VOLUME_BITMAP (vb) structure.
    # Process content of the first part of structure.
    # Separate the volume bitmap up front, so we are not making too
    # many string copies of it.
    chunk_size = struct.calcsize('2q')
    volume_bitmap = vb_struct[chunk_size:]
    vb_struct = vb_struct[:chunk_size]
    starting_lcn, vb_struct = unpack_element('q', vb_struct)    # 8 bytes
    bitmap_size, vb_struct = unpack_element('q', vb_struct)     # 8 bytes

    # If we make the GET_VOLUME_BITMAP request with 0,
    # this should always come back 0.
    assert starting_lcn == 0

    # The remaining part of the structure is the actual bitmap.
    return volume_bitmap, bitmap_size


# Retrieve info about an NTFS volume.
# We are mainly interested in the locations of the Master File Table.
# This call is currently not necessary, but has been left in to address any
# future need.
def get_ntfs_volume_data(volume_handle):
    # 512 bytes will be comfortably enough to store return object.
    vd_struct = DeviceIoControl(volume_handle, FSCTL_GET_NTFS_VOLUME_DATA,
                                None, 512)

    # At this point we have a FSCTL_GET_NTFS_VOLUME_DATA (vd) structure.
    # Pick out the elements from structure that are useful to us.
    _,              vd_struct = unpack_element('q', vd_struct)     # 8 bytes
    number_sectors, vd_struct = unpack_element('q', vd_struct)     # 8 bytes
    total_clusters, vd_struct = unpack_element('q', vd_struct)     # 8 bytes
    free_clusters,  vd_struct = unpack_element('q', vd_struct)     # 8 bytes
    total_reserved, vd_struct = unpack_element('q', vd_struct)     # 8 bytes
    _,              vd_struct = unpack_element('4I', vd_struct)    # 4*4 bytes
    _,              vd_struct = unpack_element('3q', vd_struct)    # 3*8 bytes
    mft_zone_start, vd_struct = unpack_element('q', vd_struct)     # 8 bytes
    mft_zone_end,   vd_struct = unpack_element('q', vd_struct)     # 8 bytes

    # Quick sanity check that we got something reasonable for MFT zone.
    assert (mft_zone_start < mft_zone_end and
            mft_zone_start > 0 and mft_zone_end > 0)

    logger.debug("MFT from %d to %d", mft_zone_start, mft_zone_end)
    return mft_zone_start, mft_zone_end


# Poll to confirm that our clusters were freed.
# Check ten times per second for a duration of seven seconds.
# According to Windows Internals book, it may take several seconds
# until NTFS does a checkpoint and releases the clusters.
# In later versions of Windows, this seems to be instantaneous.
def poll_clusters_freed(volume_handle, total_clusters, orig_extents):
    polling_duration_seconds = 7
    attempts_per_second = 10

    if not orig_extents:
        return True

    for _ in range(polling_duration_seconds * attempts_per_second):
        volume_bitmap, bitmap_size = get_volume_bitmap(volume_handle,
                                                       total_clusters)
        count_free, count_allocated = check_extents(
            orig_extents, volume_bitmap)
        # Some inexact measure to determine if our clusters were freed
        # by the OS, knowing that another process may grab some clusters
        # in between our polling attempts.
        if count_free > count_allocated:
            return True
        Sleep(1000 / attempts_per_second)

    return False


# Move a file (or portion of) to a new location on the disk using
# the Defrag API.
# This will raise an exception if a cluster was not free,
# or if the call failed for whatever other reason.
def move_file(volume_handle, file_handle, starting_vcn,
              starting_lcn, cluster_count):
    # Assemble input structure for our request.
    # We include a couple of zero ints for 64-bit alignment.
    input_struct = struct.pack('IIqqII', int(file_handle), 0, starting_vcn,
                               starting_lcn, cluster_count, 0)
    vb_struct = DeviceIoControl(volume_handle, FSCTL_MOVE_FILE,
                                input_struct, None)


# Write zero-fill to a file.
# Write_length is the number of bytes to be written.
def write_zero_fill(file_handle, write_length):
    # Bytearray will be initialized with null bytes as part of constructor.
    fill_string = bytearray(write_buf_size)
    assert len(fill_string) == write_buf_size

    # Loop and perform writes of write_buf_size bytes or less.
    # Continue until write_length bytes have been written.
    # There is no need to explicitly move the file pointer while
    # writing. We are writing contiguously.
    while write_length > 0:
        if write_length >= write_buf_size:
            write_string = fill_string
            write_length -= write_buf_size
        else:
            write_string = fill_string[:write_length]
            write_length = 0

        # Write buffer to file.
        #logger.debug("Write %d bytes", len(write_string))
        _, bytes_written = WriteFile(file_handle, write_string)
        assert bytes_written == len(write_string)

    FlushFileBuffers(file_handle)


# Wipe the file using the extents list we have built.
# We just rewrite the file with enough zeros to cover all clusters.
def wipe_file_direct(file_handle, extents, cluster_size, file_size):
    assert cluster_size > 0

    # Remember that file_size measures full expanded content of the file,
    # which may not always match with size on disk (eg. if file compressed).
    LockFile(file_handle, 0, 0, file_size & 0xFFFF, file_size >> 16)

    if extents:
        # Use size on disk to determine how many clusters of zeros we write.
        for lcn_start, lcn_end in extents:
            # logger.debug("Wiping extent from %d to %d...",
            #              lcn_start, lcn_end)
            write_length = (lcn_end - lcn_start + 1) * cluster_size
            write_zero_fill(file_handle, write_length)
    else:
        # Special case - file so small it can be contained within the
        # directory entry in the MFT part of the disk.
        #logger.debug("Wiping tiny file that fits entirely on MFT")
        write_length = file_size
        write_zero_fill(file_handle, write_length)


# Wipe an extent by making calls to the defrag API.
# We create a new zero-filled file, then move its clusters to the
# position on disk that we want to wipe.
# Use a look-ahead with the volume bitmap to figure out if we can expect
# our call to succeed.
# If not, break the extent into smaller pieces efficiently.
# Windows concepts:
# LCN (Logical Cluster Number) = a cluster location on disk; an absolute
#                                position on the volume we are writing
# VCN (Virtual Cluster Number) = relative position within a file, measured
#                                in clusters
def wipe_extent_by_defrag(volume_handle, lcn_start, lcn_end, cluster_size,
                          total_clusters, tmp_file_path):
    assert cluster_size > 0
    logger.debug("Examining extent from %d to %d for wipe...",
                 lcn_start, lcn_end)
    write_length = (lcn_end - lcn_start + 1) * cluster_size

    # Check the state of the volume bitmap for the extent we want to
    # overwrite. If any sectors are allocated, reduce the task
    # into smaller parts.
    # We also reduce to smaller pieces if the extent is larger than
    # 2 megabytes. For no particular reason except to avoid the entire
    # request failing because one cluster became allocated.
    volume_bitmap, bitmap_size = get_volume_bitmap(volume_handle,
                                                   total_clusters)
    # This option simulates another process that grabs clusters on disk
    # from time to time.
    # It should be moved away after QA is complete.
    if not simulate_concurrency:
        count_free, count_allocated = check_extents(
            [(lcn_start, lcn_end)], volume_bitmap)
    else:
        count_free, count_allocated = check_extents_concurrency(
            [(lcn_start, lcn_end)], volume_bitmap,
            tmp_file_path, volume_handle, total_clusters)
    if count_allocated > 0 and count_free == 0:
        return False
    if count_allocated > 0 or write_length > write_buf_size * 4:
        if lcn_start >= lcn_end:
            return False

        for split_s, split_e in split_extent(lcn_start, lcn_end):
            wipe_extent_by_defrag(volume_handle, split_s, split_e,
                                  cluster_size, total_clusters,
                                  tmp_file_path)
        return True
    # Put the zero-fill file in place.
    file_handle = CreateFile(tmp_file_path, GENERIC_READ | GENERIC_WRITE,
                             0, None, CREATE_ALWAYS,
                             FILE_ATTRIBUTE_HIDDEN, None)
    write_zero_fill(file_handle, write_length)
    new_extents = get_extents(file_handle)

    # We know the original extent was contiguous.
    # The new zero-fill file may not be contiguous, so it requires a
    # loop to be sure of reaching the end of the new file's clusters.
    new_vcn = 0
    for new_lcn_start, new_lcn_end in new_extents:
        # logger.debug("Zero-fill wrote from %d to %d",
        #                   new_lcn_start, new_lcn_end)
        cluster_count = new_lcn_end - new_lcn_start + 1
        cluster_dest = lcn_start + new_vcn

        if new_lcn_start != cluster_dest:
            logger.debug("Move %d clusters to %d",
                         cluster_count, cluster_dest)
            try:
                move_file(volume_handle, file_handle, new_vcn,
                          cluster_dest, cluster_count)
            except:
                # Move file failed, probably because another process
                # has allocated a cluster on disk.
                # Break into smaller pieces and do what we can.
                logger.debug("!! Move encountered an error !!")
                CloseHandle(file_handle)
                if lcn_start >= lcn_end:
                    return False
                for split_s, split_e in split_extent(lcn_start, lcn_end):
                    wipe_extent_by_defrag(volume_handle, split_s, split_e,
                                          cluster_size, total_clusters,
                                          tmp_file_path)
                return True
        else:
            # If Windows put the zero-fill extent on the exact clusters we
            # intended to place it, no need to attempt a move.
            logging.debug("No need to move extent from %d",
                          new_lcn_start)
        new_vcn += cluster_count

    CloseHandle(file_handle)
    DeleteFile(tmp_file_path)
    return True


# Clean up open handles etc.
def clean_up(file_handle, volume_handle, tmp_file_path):
    try:
        if file_handle:
            CloseHandle(file_handle)
        if volume_handle:
            CloseHandle(volume_handle)
        if tmp_file_path:
            DeleteFile(tmp_file_path)
    except:
        pass


# Main flow of control.
def file_wipe(file_name):
    # add \\?\ if it does not exist to support Unicode and long paths
    file_name = extended_path(file_name)
    check_os()
    win_version, _ = determine_win_version()

    volume = volume_from_file(file_name)
    volume_info = get_volume_information(volume)
    cluster_size = (volume_info.sectors_per_cluster *
                    volume_info.bytes_per_sector)

    file_handle = open_file(file_name)
    file_size, is_special = get_file_basic_info(file_name, file_handle)
    orig_extents = get_extents(file_handle)
    if is_special:
        bridged_extents = [x for x in logical_ranges_to_extents(
            get_extents(file_handle, False), True)]
    CloseHandle(file_handle)
    #logger.debug('Original extents: {}'.format(orig_extents))

    volume_handle = obtain_readwrite(volume)
    attrs = GetFileAttributesW(file_name)
    if attrs & FILE_ATTRIBUTE_READONLY:
        # Remove read-only attribute to avoid "access denied" in CreateFileW().
        SetFileAttributesW(file_name, attrs & ~FILE_ATTRIBUTE_READONLY)
    file_handle = open_file(file_name, GENERIC_READ | GENERIC_WRITE)

    if not is_special:
        # Direct overwrite when it's a regular file.
        #logger.info("Attempting direct file wipe.")
        wipe_file_direct(file_handle, orig_extents, cluster_size, file_size)
        new_extents = get_extents(file_handle)
        CloseHandle(file_handle)
        #logger.debug('New extents: {}'.format(new_extents))
        if orig_extents == new_extents:
            clean_up(None, volume_handle, None)
            return
        # Expectation was that extents should be identical and file is wiped.
        # If OS didn't give that to us, continue below and use defrag wipe.
        # Any extent within new_extents has now been wiped by above.
        # It can be subtracted from the orig_extents list, and now we will
        # just clean up anything not yet overwritten.
        orig_extents = extents_a_minus_b(orig_extents, new_extents)
    else:
        # File needs special treatment. We can't just do a basic overwrite.
        # First we will truncate it. Then chase down the freed clusters to
        # wipe them, now that they are no longer part of the file.
        truncate_file(file_handle)
        CloseHandle(file_handle)

    # Poll to confirm that our clusters were freed.
    poll_clusters_freed(volume_handle, volume_info.total_clusters,
                        orig_extents)

    # Chase down all the freed clusters we can, and wipe them.
    #logger.debug("Attempting defrag file wipe.")
    # Put the temp file in the same folder as the target wipe file.
    # Should be able to write this path if user can write the wipe file.
    tmp_file_path = os.path.dirname(file_name) + os.sep + tmp_file_name
    if is_special:
        orig_extents = choose_if_bridged(volume_handle,
                                         volume_info.total_clusters,
                                         orig_extents, bridged_extents)
    for lcn_start, lcn_end in orig_extents:
        result = wipe_extent_by_defrag(volume_handle, lcn_start, lcn_end,
                                       cluster_size, volume_info.total_clusters,
                                       tmp_file_path)

    # Clean up.
    clean_up(None, volume_handle, tmp_file_path)
    return
