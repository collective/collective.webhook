.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide.html
   This text does not appear on pypi or github. It is a comment.

==================
collective.webhook
==================

A Plone content rule action for executing HTTP GET or POST with interpolated JSON payload on content event.


Features
--------

- Can be used to trigger webhooks from Plone content rules.
- Outgoing request are pooled through Plone instance local worker thread throttled by one request / second.


Examples
--------

- Can be used to trigger CI webhook for building GatsbyJS site from Plone after each time content is being modified.


.. Documentation
   -------------

.. Full documentation for end users can be found in the "docs" folder, and is also available online at http://docs.plone.org/foo/bar


.. Translations
.. ------------

.. This product has been translated into
..
.. - Klingon (thanks, K'Plai)


Installation
------------

Install collective.webhook by adding it to your buildout::

    [buildout]

    ...

    eggs =
        collective.webhook


and then running ``bin/buildout``


Contribute
----------

- Issue Tracker: https://github.com/collective/collective.webhook/issues
- Source Code: https://github.com/collective/collective.webhook
.. - Documentation: https://docs.plone.org/foo/bar


.. Support
.. -------
..
.. If you are having issues, please let us know.
.. We have a mailing list located at: project@example.com


License
-------

The project is licensed under the GPLv2.
