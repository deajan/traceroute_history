// Extract target for traceping from current path
function getURLParameter(name) {
    return decodeURI(
        (RegExp(name + '=' + '(.+?)(&|$)').exec(location.search)||[,null])[1]
    );
}

// Add traceping output
function init () {
    var target = getURLParameter('target');
    if ( target
      && target.substring(0,1) != '_' // does not begin with a _
      && target.indexOf('.') != -1  // contains a . in it
    ) {
      // Add traceroute_history to current host view
      traceroute_history = document.createElement('div');
      traceroute_history.id = 'traceroute_history';
      traceroute_history.class = 'panel-body';
      // Only add traceroute_history to current result
      item = document.querySelectorAll('div.imgCrop_wrap').item(0);
       if (item != null) {
          item.parentElement.parentElement.appendChild(traceroute_history_div);
          fetch('/smokeping_th_helper.fcgi?target=' + target).then(data => data.text()).then(html => document.getElementById('traceroute_history').innerHTML = html);
      }
    }
}

// Load traceroute output once everything is loaded
var everythingLoaded = setInterval(function() {
  if (/loaded|complete/.test(document.readyState)) {
    clearInterval(everythingLoaded);
    init(); // this is the function that gets called when everything is loaded
  }
}, 10);
