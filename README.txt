Setting up the Sample Applications
 -The applications in this demo are intended to be hosted on Google
  App Engine. To successfully run the demo, you will need:
     > A Google account
     > The App Engine SDK and Launcher
          https://developers.google.com/appengine/downloads
     > A Google Maps API key
          https://developers.google.com/maps/documentation/javascript/tutorial#api_key
     > Google App Engine can be run on Windows, OSX, or Linux and is well supported on each platform.

 -Using Google App Engine, create a new application, which for example we
  will now on call my_samples. This will be hosted at
  my_samples.appspot.com. This name, along with the version number of
  the application, will need to be edited in the app.yaml file.
  Currently this file contains the information of Digi's version of
  these sample applications (http://map-idigi.appspot.com).

 -Before using the applications, you should edit keys_temp.py to use
  your own Google Maps API key, as well as a random string for session
  information. Then, rename keys_temp.py to keys.py. Be careful not to
  put extra whitespace in this file.

 -Using the Application Launcher provided with the SDK, use 'File' >
  'Add Existing Application' and use the directory of this README as
  the path for the application. This allows the application to be run
  locally by pointing a web browser at http://localhost:[port]. The
  application can also be deployed using the Launcher, which in our
  example causes the code to be run on the Google App Engine servers
  at http://my_sample.appspot.com.

Creating a MAP Account
 -To create a MAP account, go to https://map.idigi.com/signup/ .
  Make sure to write down your credentials, because there is no way
  to recover them.

Getting Started with MAP

 -Devices must be provisioned before they can be used. Provisioning a
  device connects the device to the iDigiMA service and allows it to
  be configured as an asset. See the Quick Start Guide at
  https://map.idigi.com/

 -To provision a device, load the sample applications and go to the
  Device application.  Add relevant device information including MAC
  address (in the form of 123456:ABCDEF) and device type, as well as
  required made up information (phone number, mobile carrier).

 -Now the device is ready to be connected to an asset. The device is
  the physical object which receives and sends data, while an asset is
  the vehicle being tracked. To create an asset with our device
  attached, use the Asset application, click on asset, and create a
  new asset. Asset Names are required to be unique (possibly only
  within an organization?)

 -Finally, new assets must be configured to work properly. Click on
  the asset in the [Assets] tab, and then click [Config]. See the Quick
  Start Guide for more information about what options need to be
  configured. Note: not configuring a device is not an option as the
  device software will not work as intended.
