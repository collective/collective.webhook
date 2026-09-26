---
myst:
  html_meta:
    "description": "Call a webhook from a Plone content rule with the collective.webhook action."
    "property=og:description": "Call a webhook from a Plone content rule with the collective.webhook action."
    "property=og:title": "collective.webhook"
    "keywords": "Plone, webhook, content rules, HTTP"
---

(index)=

# collective.webhook

`collective.webhook` adds the {guilabel}`Call webhook` action to Plone content rules.
This page shows how to call a webhook, such as the build hook of a static site host, each time content changes.

## Create a content rule

1. Open {menuselection}`Site Setup --> Content Rules` and click {guilabel}`Add content rule`.

   ```{image} /_static/content-rules.png
   :alt: The Content Rules control panel with the Add content rule button.
   :width: 740px
   ```

2. Enter a {guilabel}`Title`, choose the {guilabel}`Triggering event`, and click {guilabel}`Save`.
   For example, choose {guilabel}`Object modified` to call the webhook when an editor saves a change.

   ```{image} /_static/add-rule.png
   :alt: The Add Rule form with the title Call webhook on change and the event Object modified.
   :width: 740px
   ```

## Add the webhook action

1. Choose {guilabel}`Call webhook` in the {guilabel}`Action` list and click {guilabel}`Add`.

   ```{image} /_static/add-action.png
   :alt: The rule page with Call webhook selected in the Action list.
   :width: 740px
   ```

2. Fill in the form and click {guilabel}`Save`.

   ```{image} /_static/webhook-action.png
   :alt: The Add Webhook Action form filled in with a URL, the POST method, and a JSON payload.
   :width: 740px
   ```

   {guilabel}`Webhook URL`
   :   The URL to call, such as the build hook URL from your hosting service.

   {guilabel}`Call method`
   :   `GET`, `POST` or `POST FORM`.
       Choose `POST` unless your service documents another method.

   {guilabel}`JSON payload`
   :   The data to send, as JSON.
       Always fill in this field, and use `{}` when you have nothing to send.
       To send values from the content, use variables such as `${title}` and `${url}`.
       The table below the form lists all the variables.

   {guilabel}`JSON headers`
   :   Optional.
       A JSON object of headers, for example `{"Authorization": "Bearer my-secret-token"}`.

   {guilabel}`Verbose logging`
   :   Optional.
       Select it to write the request and the response to the Plone log while you test.

## Apply the rule

Click {guilabel}`Apply rule on the whole site` on the rule page.

```{image} /_static/apply-rule.png
:alt: The rule page with the Call webhook action and the Apply rule on the whole site button.
:width: 740px
```

Plone now calls the webhook each time the triggering event happens.
