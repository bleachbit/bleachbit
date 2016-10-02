# How to contribute to BleachBit

Thank you for your interest in contributing. Following these changes will help get them merged sooner.

If you plan to write a major change, please consider first emailing to discuss.

## Environment

BleachBit runs on Python 2.5, 2.6, and 2.7 with PyGTK 2. See also [running from source](https://docs.bleachbit.org/dev/running-from-source-code.html) regarding dependencies.

The modernization branch supports GTK+ 3, but it is not yet ready. See the GitHub issues.

## Procedure

* Get a GitHub account.
* Fork the right BleachBit repository, as there are several repositories.
* Check out your forked repository.
* Make your changes.
* Test your changes.
* Consider adding or expanding a unit test.
* Run the unit tests by running
````
python tests/TestAll.py
````
* Make commits in small, logical units to make them easier to review.
* Submit one pull request.

If you have multiple commits around multiple themes (such as adding two, unrelated features), please consider breaking them up into multiple pull requests by using multiple branches. Smaller pull requests are easier to review and commit.

## Style
* Indent with four spaces instead of tabs.
* Format your code using PEP-8 standards like this:
````autopep8 -i bleachbit/Action.py````
* Follow other best practices, such as writing some documentation in the code.

