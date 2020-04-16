# Change Log
## [Unreleased]
### Changed
- A super user token is no longer required to instantiate a `ShinobiClient`. A
  `ShinobiSuperUserCredentialsRequiredError` will be raised at the point at which it is needed if it has not been
  supplied.
- Details about a user can be queried without a super user token.
- A user's API key can be attained without a super user token.
- More specialised errors.

### Added
- Monitor ORM.

## 1.0.0
Initial release.
