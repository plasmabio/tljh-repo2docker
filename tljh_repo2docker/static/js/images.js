require(["jquery", "bootstrap", "moment", "jhapi", "utils"], function(
  $,
  bs,
  moment,
  JHAPI,
  utils
) {
  "use strict";

  var base_url = '/services/environments';
  var api = new JHAPI(base_url);

  function getRow(element) {
    var original = element;
    while (!element.hasClass("image-row")) {
      element = element.parent();
      if (element[0].tagName === "BODY") {
        console.error("Couldn't find row for", original);
        throw new Error("No image-row found");
      }
    }
    return element;
  }

  $("#add-environment").click(function() {
    var dialog = $("#create-environment-dialog");
    dialog.find(".repo-input").val("");
    dialog.find(".ref-input").val("");
    dialog.find(".memory-input").val("");
    dialog.find(".cpu-input").val("");
    dialog.modal();
  });

  $("#create-environment-dialog")
    .find(".save-button")
    .click(function() {
      var dialog = $("#create-environment-dialog");
      var repo = dialog.find(".repo-input").val();
      var ref = dialog.find(".ref-input").val().trim();
      var memory = dialog.find(".memory-input").val().trim();
      var cpu = dialog.find(".cpu-input").val().trim();
      var spinner = $("#adding-environment-dialog");
      spinner.find('.modal-footer').remove();
      spinner.modal();
      api.api_request("build", {
        type: "POST",
        data: JSON.stringify({
          repo: repo,
          ref: ref,
          memory: memory,
          cpu: cpu
        }),
        dataType: null,
        success: function(reply) {
          window.location.reload();
        },
      });
    });

  $(".remove-environment").click(function() {
    var el = $(this);
    var row = getRow(el);
    var image = row.data("image");
    var dialog = $("#remove-environment-dialog");
    dialog.find(".delete-environment").text(image);
    dialog.modal();
  });

  $("#remove-environment-dialog")
    .find(".remove-button")
    .click(function() {
      var dialog = $("#remove-environment-dialog");
      var image = dialog.find(".delete-environment").text();
      var spinner = $("#removing-environment-dialog");
      spinner.find('.modal-footer').remove();
      spinner.modal();
      api.api_request("build", {
        type: "DELETE",
        data: JSON.stringify({
          name: image
        }),
        dataType: null,
        success: function(reply) {
          window.location.reload();
        },
      })
    });
});
