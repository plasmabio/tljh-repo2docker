require(["jquery", "bootstrap", "moment", "jhapi", "utils"], function(
  $,
  bs,
  moment,
  JHAPI,
  utils
) {
  "use strict";

  var base_url = window.jhdata.base_url;
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
    dialog.find(".name-input").val("");
    dialog.find(".memory-input").val("");
    dialog.find(".cpu-input").val("");
    dialog.modal();
  });

  $("#create-environment-dialog")
    .find(".save-button")
    .click(function() {
      var dialog = $("#create-environment-dialog");
      var repo = dialog.find(".repo-input").val().trim();
      var ref = dialog.find(".ref-input").val().trim();
      var name = dialog.find(".name-input").val().trim();
      var memory = dialog.find(".memory-input").val().trim();
      var cpu = dialog.find(".cpu-input").val().trim();
      var spinner = $("#adding-environment-dialog");
      spinner.find('.modal-footer').remove();
      spinner.modal();
      api.api_request("environments", {
        type: "POST",
        data: JSON.stringify({
          repo: repo,
          ref: ref,
          name: name,
          memory: memory,
          cpu: cpu
        }),
        success: function() {
          window.location.reload();
        },
      });
    });

  $(".remove-environment").click(function() {
    var el = $(this);
    var row = getRow(el);
    var image = row.data("image");
    var name = row.data("display-name");
    var dialog = $("#remove-environment-dialog");
    dialog.find(".delete-environment").attr("data-image", image);
    dialog.find(".delete-environment").text(name);
    dialog.modal();
  });

  $("#remove-environment-dialog")
    .find(".remove-button")
    .click(function() {
      var dialog = $("#remove-environment-dialog");
      var image = dialog.find(".delete-environment").data("image");
      var spinner = $("#removing-environment-dialog");
      spinner.find('.modal-footer').remove();
      spinner.modal();
      api.api_request("environments", {
        type: "DELETE",
        data: JSON.stringify({
          name: image
        }),
        success: function() {
          window.location.reload();
        },
      })
    });

  // initialize tooltips
  $('[data-toggle="tooltip"]').tooltip();

});
