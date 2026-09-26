# Changelog

## 0.3.2 (unreleased)

- Fix POST webhooks sending custom headers as form data instead of headers
  and dropping the JSON payload
- Fix GET webhooks not sending custom headers
- Fix `create_tarball` test helper failing on nested directories
- Add tests for submit, interpolation, data manager, executor and validators

## 0.3.1 (2024-05-28)

- Add minimal Python 3 compatibility
  [Asko Soukka]

## 0.3.0 (2018-12-05)

- Add buildout for Plone 4.3
  [Asko Soukka]

## 0.2.1 (2018-06-04)

- Fix typo in vocabulary value title
  [Asko Soukka]

## 0.2 (2018-06-04)

- Add dedicated method POST FORM for HTTP POST with Content-Type:
  application/x-www-form-urlencoded
  [datakurre]

## 0.1 (2018-05-27)

- Initial release.
  [datakurre]
