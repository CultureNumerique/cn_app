
// must have url and is_home, base_url defined previously (likely in form_edition.html)
// this script add a listener to the window and launch the preview update whenever an event is thrown at it.
// The event comes from etherpad whenever a change is made into the pad. (thrown from collab_client.js -> handleMessageFromServer)

  var can_update = true;
  var waiting = false;

  // occur after we detect a change in the pad's content and 5 seconds has passed
  function setValue(){
    can_update=true;
    waiting=false;
    feedback=document.getElementById("feedback").checked;
    update_preview(base_url,feedback);
  }

  // update the iframe
  // call convertir_module and convertir_home in etherpad_process.js
  function update_preview(url_base,feedback){
    if (is_home){
      convertir_home(url_base,url_module,feedback);
    }
    else{
      convertir_module(url_base,url_module,feedback);
    }
  }

  // occur after we detect a change in the pad's content
  // wait for 5 seconds, then update the preview in the other iframe
  function receiver(e) {
    if(!waiting){
     window.setTimeout("setValue()",5000);
     waiting=true;
    }
    if(can_update){
      can_update=false;
    }

  }

  // add the listener to the window
  function addlistener(){
    if (!window.addEventListener) {
       window.attachEvent('onmessage', receiver);
   } else {
       window.addEventListener('message', receiver, false);
   }

  }
