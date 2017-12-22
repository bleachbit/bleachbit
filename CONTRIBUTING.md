# How to contribute to BleachBit

Thank you for your interest in contributing.


## When to file a bug report

Are you using the [latest version](https://www.bleachbit.org/download)?

## Where to file an issue

Most bug reports should be filed in [GitHub under the BleachBit repository](https://github.com/bleachbit/bleachbit/issues/new).

Bug reports were managed in [Launchpad](https://bugs.launchpad.net/bleachbit/) between about 2009 and 2016. Launchpad still contains some active issue tickets, but more recently users are encouraged to file issue tickets in GitHub.


## Information to include with bug reports

When filing a bug report, please include:
* The version of BleachBit
* The type and version of the operating system (for example, Windows 10 or Ubuntu 16.04)
* The exact error message
* Which exact steps you took before the error happened

If you are reporting an error that happens while cleaning ([example screenshot](https://user-images.githubusercontent.com/22394276/31048383-42d469d8-a61c-11e7-9a7d-d149887ce2f3.jpg)), please try to narrow it down a single cleaning option (in other words, a single checkbox).

See also [prioritization of issues](https://www.bleachbit.org/contribute/prioritization-issues).


## Development environment

BleachBit runs on Python 2.7 with PyGTK 2. See also [running from source](https://docs.bleachbit.org/dev/running-from-source-code.html) regarding dependencies.

The modernization branch supports GTK+ 3, but it is not yet ready. See the GitHub issues.


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


## Style
* Indent with four spaces instead of tabs.
* Format your code using PEP-8 standards like this:
````autopep8 -i bleachbit/Action.py````
* Follow other best practices such as they relate to readability, documentation, error handling, and performance.

