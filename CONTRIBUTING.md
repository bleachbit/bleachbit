# How to contribute to BleachBit

Thank you for your interest in contributing.


## Filing issues

Most bug reports are managed in [Launchpad](http://bugs.launchpad.net/) for historical reasons. BleachBit has been using Launchpad since at least 2009.

Most users should use Launchpad to file bug reports for the BleachBit applications, but please file issues in GitHub for these exceptions:
* You plan to commit the code that will close the issue.
* The issue is specific to one of the special repositories (i.e., CleanerML, Winapp2.ini, bleachbit-misc).

When filing a bug report, please include:
* The version of BleachBit
* The type and version of the operating system (for example, Windows 10 or Ubuntu 16.04)
* The exact error message
* Which exact steps you took before the error happened

See also [prioritization of issues](https://www.bleachbit.org/contribute/prioritization-issues).


## Development environment

BleachBit runs on Python 2.5, 2.6, and 2.7 with PyGTK 2. See also [running from source](https://docs.bleachbit.org/dev/running-from-source-code.html) regarding dependencies.

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
* Check that it passes the tests by Travis CI and Appveyor.

If you have multiple commits around multiple themes (such as adding two, unrelated features), please consider breaking them up into multiple pull requests by using multiple branches. Smaller pull requests are easier to review and commit.


## Style
* Indent with four spaces instead of tabs.
* Format your code using PEP-8 standards like this:
````autopep8 -i bleachbit/Action.py````
* Follow other best practices such as they relate to readability, documentation, error handling, and performance.

