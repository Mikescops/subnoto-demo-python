angular.module("quoteApp", [])
  .controller("QuoteController", function ($http, $sce, $timeout) {
    var vm = this;
    var embedOrigin = null;

    function toLocalDateStr(d) {
      var y = d.getFullYear();
      var m = String(d.getMonth() + 1).padStart(2, "0");
      var day = String(d.getDate()).padStart(2, "0");
      return y + "-" + m + "-" + day;
    }

    function defaultDate(offsetDays) {
      var d = new Date();
      d.setDate(d.getDate() + (offsetDays || 0));
      return toLocalDateStr(d);
    }

    function randomInvNumber() {
      return "INV-" + Date.now().toString(36).toUpperCase().slice(-6);
    }

    function sampleFormData(keepEmail) {
      return {
        email: keepEmail && vm.form && vm.form.email ? vm.form.email : "demo@example.com",
        firstname: "Demo",
        lastname: "Signer",
        title: "Invoice – Consulting Q1",
        amount: "0",
        description: "",
        quoteNumber: randomInvNumber(),
        quoteDate: defaultDate(0),
        validityDate: defaultDate(30),
        clientName: "Jane Smith",
        company: "Acme Solutions Ltd",
        address: "12 High Street, London SW1A 1AA",
        lineDescription: "Web development & consulting",
        lineQuantity: 2,
        lineUnitPrice: 1250,
        taxRatePercent: 20
      };
    }

    vm.getDefaultDate = function (offsetDays) {
      return defaultDate(offsetDays == null ? 0 : offsetDays);
    };

    vm.form = sampleFormData(false);
    $timeout(function () {
      vm.form.quoteDate = defaultDate(0);
      vm.form.validityDate = defaultDate(30);
    }, 0);

    vm.fillWithSample = function () {
      vm.form = sampleFormData(true);
    };
    vm.whoami = null;
    vm.iframeUrl = null;
    vm.error = null;
    vm.loading = false;
    vm.signedMessage = null;

    vm.dismissSignedMessage = function () {
      vm.signedMessage = null;
    };

    function normalizeOrigin(url) {
      if (!url) return "";
      try {
        return new URL(url).origin.replace(/\/$/, "").toLowerCase();
      } catch (e) {
        return "";
      }
    }

    function handleEmbedMessage(event) {
      if (!event.data || event.data.type !== "subnoto:documentSigned") return;
      var expected = embedOrigin ? normalizeOrigin(embedOrigin) : "";
      var originNorm = normalizeOrigin(event.origin);
      var isLocalhost = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
      var originOk = !expected || originNorm === expected || isLocalhost;
      if (!originOk) return;
      var payload = event.data.payload;
      if (!payload || typeof payload.envelopeUuid !== "string" || typeof payload.completed !== "boolean") return;
      $timeout(function () {
        vm.signedMessage = payload.completed
          ? "Document signed successfully. All signers have completed the envelope."
          : "Your signature has been recorded. Other signers may still need to sign.";
      });
    }

    window.addEventListener("message", handleEmbedMessage);

    $http.get("/api/whoami").then(function (res) {
      vm.whoami = res.data;
      console.log("[quote] whoami response", vm.whoami);
      if (vm.whoami && vm.whoami.ownerEmail) {
        vm.form.email = vm.whoami.ownerEmail;
      }
      vm.form.quoteDate = vm.form.quoteDate || defaultDate(0);
      vm.form.validityDate = vm.form.validityDate || defaultDate(30);
      if (vm.whoami && vm.whoami.error) {
        console.warn("[quote] whoami error:", vm.whoami.error);
      }
    }).catch(function (err) {
      console.error("[quote] whoami request failed", err.status, err.data);
      vm.whoami = { error: err.data && err.data.error ? err.data.error : "Could not load environment" };
    });

    vm.createQuote = function () {
      vm.error = null;
      vm.iframeUrl = null;
      vm.signedMessage = null;
      vm.loading = true;

      var payload = {
        email: vm.form.email,
        firstname: vm.form.firstname,
        lastname: vm.form.lastname,
        title: vm.form.title,
        amount: String(vm.form.lineQuantity * vm.form.lineUnitPrice || vm.form.amount || 0),
        description: vm.form.lineDescription || vm.form.description || "",
        quoteNumber: vm.form.quoteNumber,
        quoteDate: vm.form.quoteDate,
        validityDate: vm.form.validityDate,
        clientName: vm.form.clientName,
        company: vm.form.company,
        address: vm.form.address,
        taxRatePercent: vm.form.taxRatePercent,
        lineItems: [
          {
            description: vm.form.lineDescription || "Item",
            quantity: Number(vm.form.lineQuantity) || 1,
            unitPrice: Number(vm.form.lineUnitPrice) || 0
          }
        ]
      };

      console.log("[quote] createQuote payload", payload);
      $http.post("/api/quotes/create", payload)
        .then(function (res) {
          console.log("[quote] createQuote response", res.data);
          if (res.data && res.data.iframeUrl) {
            vm.iframeUrl = $sce.trustAsResourceUrl(res.data.iframeUrl);
            embedOrigin = res.data.iframeUrl;
          } else {
            vm.error = res.data && res.data.error ? res.data.error : "No iframe URL returned";
            console.warn("[quote] createQuote no iframeUrl", vm.error);
          }
        })
        .catch(function (err) {
          vm.error = (err.data && err.data.error) ? err.data.error : (err.statusText || "Request failed");
          console.error("[quote] createQuote failed", err.status, err.data, vm.error);
        })
        .finally(function () {
          vm.loading = false;
        });
    };
  });
