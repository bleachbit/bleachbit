# How to contribute to BleachBit

Thank you for your interest in contributing.


## When to file a bug report

If you are not using the [latest stable version](https://www.bleachbit.org/download), try upgrading. Windows users can also try [CI builds](https://ci.bleachbit.org/).

If you are on the latest, stable version, check "known issues" section of [release notes](https://www.bleachbit.org/news).

## Where to file an issue

Most bug reports should be filed in [GitHub under the BleachBit repository](https://github.com/bleachbit/bleachbit/issues/new).

Bug reports were managed in [Launchpad](https://bugs.launchpad.net/bleachbit/) between about 2009 and 2016. Launchpad still contains some active issue tickets, but more recently users are encouraged to file issue tickets in GitHub.


## Information to include with bug reports

When filing a [bug report](https://github.com/bleachbit/bleachbit/issues/new), the issue template will guide you on which information to include.

If you are reporting an error that happens while cleaning ([example screenshot](https://user-images.githubusercontent.com/22394276/31048383-42d469d8-a61c-11e7-9a7d-d149887ce2f3.jpg)), please try to narrow it down a single cleaning option (in other words, a single checkbox).

Three kinds of information are often helpful:

1. Screenshot: to include a screenshot, you can either drag-and-drop it like a file attachment or use CTRL+V to paste it from the clipboard into the GitHub comment form.

2. BleachBit log: this is the text that BleachBit shows while it is running. You can copy and paste it as text. Do not include hundreds of lines, but try to narrow it down to the interesting parts, like error messages. [Enabling debug logging](https://docs.bleachbit.org/doc/troubleshooting.html) using the launcher or preferences may show more information.

3. BleachBit [system information](https://docs.bleachbit.org/doc/troubleshooting.html): this is a window inside of BleachBit that includes general information about your system. Copy and paste this as text, and paste it into GitHub.

See also [prioritization of issues](https://www.bleachbit.org/contribute/prioritization-issues).


## Development environment

BleachBit 4.x runs on Python 3 with GTK 3. See also [running from source](https://docs.bleachbit.org/dev/running-from-source-code.html) regarding dependencies.


## Procedure for creating and submitting patch

Following this process will help your changes get merged sooner. If you plan to write a major change, please consider first opening a GitHub issue to discuss.

* Log in to GitHub.
* Fork the right BleachBit repository, as there are several repositories.
* Check out your forked repository.
* Make your changes.
* Test your changes. Consider adding or expanding a unit test.
* Run the unit tests by running
````
python tests/TestAll.py
````
* Make commits in small, logical units to make them easier to review.
* Submit the pull request.
* Check that it passes the tests by Travis CI and AppVeyor.

If you have multiple commits around multiple themes (such as adding two, unrelated features), please consider breaking them up into multiple pull requests by using multiple branches. Smaller pull requests are easier to review and commit.

Please consider reviewing someone else's pull requests and asking him or her to do the same for you. This can improve quality and get your changes merged sooner.


## Coding style

* Indent with four spaces instead of tabs.
* Format your code using PEP-8 standards like this:
````autopep8 -i bleachbit/Action.py````
* Follow other best practices such as they relate to readability, documentation, error handling, and performance.
* See OpenStack [Git Commit Good Practice](https://wiki.openstack.org/wiki/GitCommitMessages) for advice on writing good Git commit messages. In particular, the first line of the commit message is important.
