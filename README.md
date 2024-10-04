# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/openedx/platform-plugin-aspects/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                                           |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| platform\_plugin\_aspects/\_\_init\_\_.py                                      |        4 |        0 |        0 |        0 |    100% |           |
| platform\_plugin\_aspects/apps.py                                              |        9 |        0 |        0 |        0 |    100% |           |
| platform\_plugin\_aspects/extensions/\_\_init\_\_.py                           |        0 |        0 |        0 |        0 |    100% |           |
| platform\_plugin\_aspects/extensions/filters.py                                |       35 |        2 |        2 |        1 |     92% |42-43, 46->51 |
| platform\_plugin\_aspects/management/\_\_init\_\_.py                           |        0 |        0 |        0 |        0 |    100% |           |
| platform\_plugin\_aspects/management/commands/\_\_init\_\_.py                  |        0 |        0 |        0 |        0 |    100% |           |
| platform\_plugin\_aspects/management/commands/dump\_data\_to\_clickhouse.py    |       64 |        0 |       16 |        0 |    100% |           |
| platform\_plugin\_aspects/management/commands/load\_test\_tracking\_events.py  |      111 |        0 |        6 |        0 |    100% |           |
| platform\_plugin\_aspects/management/commands/monitor\_load\_test\_tracking.py |      157 |        5 |       16 |        2 |     95% |158->162, 176-184 |
| platform\_plugin\_aspects/signals.py                                           |       33 |        8 |       10 |        1 |     60% |77-93, 133->exit, 191, 229, 267 |
| platform\_plugin\_aspects/sinks/\_\_init\_\_.py                                |        7 |        0 |        0 |        0 |    100% |           |
| platform\_plugin\_aspects/sinks/base\_sink.py                                  |      151 |        0 |       38 |        0 |    100% |           |
| platform\_plugin\_aspects/sinks/course\_enrollment\_sink.py                    |       11 |        0 |        0 |        0 |    100% |           |
| platform\_plugin\_aspects/sinks/course\_overview\_sink.py                      |       96 |        0 |       22 |        0 |    100% |           |
| platform\_plugin\_aspects/sinks/external\_id\_sink.py                          |       11 |        0 |        0 |        0 |    100% |           |
| platform\_plugin\_aspects/sinks/serializers.py                                 |       81 |        7 |        6 |        2 |     87% |30, 32-35, 208, 232, 257 |
| platform\_plugin\_aspects/sinks/tag\_sink.py                                   |       23 |        0 |        0 |        0 |    100% |           |
| platform\_plugin\_aspects/sinks/user\_profile\_sink.py                         |       11 |        0 |        0 |        0 |    100% |           |
| platform\_plugin\_aspects/sinks/user\_retire\_sink.py                          |       22 |        0 |        4 |        0 |    100% |           |
| platform\_plugin\_aspects/tasks.py                                             |       21 |        0 |       14 |        0 |    100% |           |
| platform\_plugin\_aspects/urls.py                                              |        5 |        0 |        0 |        0 |    100% |           |
| platform\_plugin\_aspects/utils.py                                             |      105 |        0 |       30 |        0 |    100% |           |
| platform\_plugin\_aspects/views.py                                             |       51 |        0 |        2 |        0 |    100% |           |
| platform\_plugin\_aspects/waffle.py                                            |        1 |        0 |        0 |        0 |    100% |           |
| platform\_plugin\_aspects/xblock.py                                            |       72 |        0 |       21 |        0 |    100% |           |
|                                                                      **TOTAL** | **1081** |   **22** |  **187** |    **6** | **97%** |           |


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