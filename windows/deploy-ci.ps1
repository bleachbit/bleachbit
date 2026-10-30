# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.

# For CI, upload the Windows build artifacts in the current directory to
# the S3 bucket behind download.bleachbit.org/ci and list them in the job
# summary. Needs VERSION, AWS_BUCKET_NAME and the AWS credentials.

$ErrorActionPreference = 'Stop'

# Sanitize
$ref = ($env:GITHUB_REF_NAME -replace '[^A-Za-z0-9._/-]','_')
$ver = ($env:VERSION         -replace '[^A-Za-z0-9._-]','_')
$run = $env:GITHUB_RUN_NUMBER
$runId = $env:GITHUB_RUN_ID
$attempt = $env:GITHUB_RUN_ATTEMPT
$event = ($env:GITHUB_EVENT_NAME -replace '[^A-Za-z0-9._-]','_')
$actor = ($env:GITHUB_TRIGGERING_ACTOR -replace '[^A-Za-z0-9._@-]','_')
$sha = $env:GITHUB_SHA.Substring(0,8)
# Three-part version (APP_VERSION without the run number suffix)
$ver3 = (($ver -split '\.')[0..2] -join '.')
$branch = ''
$tag = ''
if ($env:GITHUB_REF_TYPE -eq 'tag') { $tag = $ref } else { $branch = $ref }
$dest = "s3://$env:AWS_BUCKET_NAME/"
"## Windows CI builds`n" >> $env:GITHUB_STEP_SUMMARY
Get-ChildItem BleachBit-*-setup.exe, BleachBit-*-setup-English.exe, BleachBit-*-portable.zip -File |
  ForEach-Object {
    $file = $_.FullName
    $name = $_.Name
    $sha256 = (Get-FileHash -Algorithm SHA256 $file).Hash.ToLower()
    $sha1   = (Get-FileHash -Algorithm SHA1   $file).Hash.ToLower()
    $md5    = (Get-FileHash -Algorithm MD5    $file).Hash.ToLower()
    $artifactType = if ($name -like '*-setup-English.exe') { 'installer-english' } `
                    elseif ($name -like '*-setup.exe') { 'installer' } `
                    elseif ($name -like '*-portable.zip') { 'portable' } `
                    else { 'unknown' }
    $meta = "ref=$ref,run=$run,run_id=$runId,attempt=$attempt,event=$event,actor=$actor,version=$ver,version3=$ver3,commit=$sha,branch=$branch,tag=$tag,sha256=$sha256,sha1=$sha1,md5=$md5,size=$($_.Length),artifact_type=$artifactType,frontend=gtk"
    $url = "https://download.bleachbit.org/ci/$name"
    Write-Output ("{0,15:N0} bytes  {1}  ->  {2}" -f $_.Length, $name, $url)
    aws s3 cp $file "$dest" --metadata "$meta"
    if ($LASTEXITCODE -ne 0) { throw "upload of $name failed with exit code $LASTEXITCODE" }
    "- [$name]($url) ({0:N0} bytes)" -f $_.Length >> $env:GITHUB_STEP_SUMMARY
  }
$filter = if ($tag) { "tag=$tag" } else { "branch=$branch" }
$indexUrl = "https://download.bleachbit.org/ci/#$filter"
Write-Output "Index: $indexUrl"
"`n[All builds for this $($filter.Split('=')[0])]($indexUrl)" >> $env:GITHUB_STEP_SUMMARY
