# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/openedx/platform-plugin-aspects/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                                           |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| platform\_plugin\_aspects/\_\_init\_\_.py                                      |        4 |        0 |        0 |        0 |    100% |           |
| platform\_plugin\_aspects/apps.py                                              |        9 |        0 |        0 |        0 |    100% |           |
| platform\_plugin\_aspects/extensions/\_\_init\_\_.py                           |        0 |        0 |        0 |        0 |    100% |           |
| platform\_plugin\_aspects/extensions/filters.py                                |       36 |        2 |        2 |        1 |     92% |42-43, 46->51 |
| platform\_plugin\_aspects/management/\_\_init\_\_.py                           |        0 |        0 |        0 |        0 |    100% |           |
| platform\_plugin\_aspects/management/commands/\_\_init\_\_.py                  |        0 |        0 |        0 |        0 |    100% |           |
| platform\_plugin\_aspects/management/commands/dump\_data\_to\_clickhouse.py    |       64 |        0 |       16 |        0 |    100% |           |
| platform\_plugin\_aspects/management/commands/load\_test\_tracking\_events.py  |      112 |        1 |        6 |        0 |     99% |       214 |
| platform\_plugin\_aspects/management/commands/monitor\_load\_test\_tracking.py |      156 |        7 |       16 |        2 |     94% |93, 142, 157->161, 175-183 |
| platform\_plugin\_aspects/signals.py                                           |       13 |        0 |        0 |        0 |    100% |           |
| platform\_plugin\_aspects/sinks/\_\_init\_\_.py                                |        5 |        0 |        0 |        0 |    100% |           |
| platform\_plugin\_aspects/sinks/base\_sink.py                                  |      151 |        9 |       38 |        2 |     94% |84, 90, 96, 102, 107, 113, 119, 125, 130, 341->340, 364->363 |
| platform\_plugin\_aspects/sinks/course\_overview\_sink.py                      |       81 |        0 |       18 |        1 |     99% |  138->137 |
| platform\_plugin\_aspects/sinks/external\_id\_sink.py                          |       11 |        0 |        0 |        0 |    100% |           |
| platform\_plugin\_aspects/sinks/serializers.py                                 |       43 |        0 |        0 |        0 |    100% |           |
| platform\_plugin\_aspects/sinks/user\_profile\_sink.py                         |       11 |        0 |        0 |        0 |    100% |           |
| platform\_plugin\_aspects/sinks/user\_retire\_sink.py                          |       22 |        0 |        4 |        0 |    100% |           |
| platform\_plugin\_aspects/tasks.py                                             |       19 |        0 |       14 |        6 |     82% |19->21, 20->19, 21->20, 43->45, 44->43, 45->44 |
| platform\_plugin\_aspects/urls.py                                              |        5 |        0 |        0 |        0 |    100% |           |
| platform\_plugin\_aspects/utils.py                                             |      110 |        0 |       32 |        0 |    100% |           |
| platform\_plugin\_aspects/views.py                                             |       51 |        0 |        2 |        0 |    100% |           |
| platform\_plugin\_aspects/waffle.py                                            |        1 |        0 |        0 |        0 |    100% |           |
| platform\_plugin\_aspects/xblock.py                                            |       79 |        3 |       21 |        4 |     93% |22-24, 37->39, 38->37, 183->182, 202->201 |
|                                                                      **TOTAL** |  **983** |   **22** |  **169** |   **16** | **97%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/openedx/platform-plugin-aspects/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/openedx/platform-plugin-aspects/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/openedx/platform-plugin-aspects/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/openedx/platform-plugin-aspects/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fopenedx%2Fplatform-plugin-aspects%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/openedx/platform-plugin-aspects/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.