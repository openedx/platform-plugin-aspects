Change Log
##########

..
   All enhancements and patches to platform_plugin_aspects will be documented
   in this file.  It adheres to the structure of https://keepachangelog.com/ ,
   but in reStructuredText instead of Markdown (for ease of incorporation into
   Sphinx documentation and the PyPI description).

   This project adheres to Semantic Versioning (https://semver.org/).

.. There should always be an "Unreleased" section for changes pending release.

Unreleased
**********

0.9.1 - 2024-05-08
******************

Fixes
=====

* Fix an ImportError in the Aspects Xblock on pre-Quince releases


0.9.0 - 2024-05-06
******************

Added
=====

* Allow embedded dashboard tab names to be localized

0.8.0 - 2024-05-06
******************

Added
=====

* Added tags to xblocks in course dump


0.7.4 - 2024-04-30
******************

Fixed
=====
* Fixed Superset XBlock and default filters.

0.7.3 - 2024-04-30
******************

Fixed
=====

* Fixed UUID generation for localized Superset assets, which caused embedded
  dashboards to fail to load when localized.

0.7.2 - 2024-04-19
******************

Fixed
=====

* Fixed cms url configuration

0.7.1 - 2024-04-17
******************

Fixed
=====

* Fixed issue with embedded dashboards throwing javascript errors
* Fixed issues with translated embedded dashboards erroring in Superset

0.7.0 - 2024-04-12
******************

Added
=====

* Add endpoint for fetchGuestToken

0.6.0 - 2024-04-08
******************

Added
=====

* Allow to embed translated Superset Dashboards.

0.5.0 - 2024-04-01
******************

Added
=====

* Load testing and test monitoring scripts.

0.4.0 - 2024-03-18
******************

Added
=====

* Embed multiple Superset Dashboards.

0.3.1 - 2024-03-14
******************

Added
=====

* Fixed development server configuration.

0.3.0 – 2024-03-10
******************

Added
=====

* Imported XBlock code from platform-plugin-superset

0.2.0 – 2024-03-05
******************

Added
=====

* Imported code from event-sink-clickhouse.

0.1.0 – 2024-02-29
**********************************************

Added
=====

* First release on PyPI.
