/* Javascript for SupersetXBlock. */
function SupersetXBlock(runtime, element) {

  $(element).find('.save-button').bind('click', function() {
      var handlerUrl = runtime.handlerUrl(element, 'studio_submit');
      var data = {
          display_name: $(element).find('input[name=superset_display_name]').val(),
          dashboard_uuid: $(element).find('input[name=superset_dashboard_uuid]').val(),
          filters: $(element).find('input[name=superset_filters]').val(),
      };
      $.post(handlerUrl, JSON.stringify(data)).done(function(response) {
        window.location.reload(false);
      });
    });

  $(element).find('.cancel-button').bind('click', function() {
      runtime.notify('cancel', {});
  });
}
