try {
  (function (require) {
    require.config({
      paths: {
        supersetEmbeddedSdk: "https://cdn.jsdelivr.net/npm/@superset-ui/embedded-sdk@0.1.0-alpha.10/bundle/index.min",
      },
    });
  }).call(this, require || RequireJS.require);
} catch (e) {
  console.log("Unable to load embedded_sdk via requirejs");
}
