# Change Log
## [Unreleased]
### Changed
- A super user token is no longer required to instantiate a `ShinobiClient`. A
  `ShinobiSuperUserCredentialsRequiredError` will be raised at the point at which it is needed if it has not been
  supplied.

## 1.0.0
Initial release.
