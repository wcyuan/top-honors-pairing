var express = require('express')
  , http    = require('http')
  , path    = require('path');

/*
  Initialize the Express app, the E in the MEAN stack (from mean.io).

  Templates: First, we configure the directory in which the Express app will
  look for templates, as well as the engine it'll use to interpret them (in
  this case Embedded JS). So we can use the views/orderpage.ejs and
  views/homepage.ejs files in response.render (see routes.js).

  Port: We then set up the port that the app will listen on by parsing the
  variable that's configured in .env (or else using a default).

  Static file serving: Then we set up express for static file serving, by
  making the entire content under '/public' accessible on the WWW. Thus
  every file <file-name> in /public is served at example.com/<file-name>. We
  specifically instruct the app to look for a particular file called the
  favicon.ico; this is what browsers use to represent minified sites in
  tabs, bookmarks, and favorites (hence 'favicon = favorite icon'). By
  default the query would go to example.com/favicon.ico, but we redirect it
  to example.com/public/img/favicon.ico as shown.

  Logging: We set up a convenient dev logger so that you can watch
  network requests to express in realtime. Run foreman start in the home
  directory after following the instructions in README.md and Express
  will begin printing logging information to the command line.

  Routes: We have separated the routing information into a separate
  routes.js file, which we import. This tell the app what function to
  execute when a client accesses a URL like example.com/ or
  example.com/orders. See routes.js for more details.

  Init: Finally, we start the HTTP server.

*/

var app = express();
app.set('views', __dirname + '/views');
app.set('view engine', 'ejs');
app.set('port', process.env.PORT || 8080);
app.use(express.static(path.join(__dirname, 'public')));
//app.use(express.favicon(path.join(__dirname, 'public/img/favicon.ico')));
app.use(express.logger("dev"));

/*
var ROUTES  = require('./routes');
for(var ii in ROUTES) {
    app.get(ROUTES[ii].path, ROUTES[ii].fn);
}
*/

// Begin listening for HTTP requests to Express app
http.createServer(app).listen(app.get('port'), function() {
    console.log("Listening on " + app.get('port'));
});
