
// DOM manipulation used in the simple course generation form

var nb_module=1;

// remove a module from the form
function removeModule(){
  if(nb_module>1){
    var module= document.getElementById('module'+nb_module);
    var modules= document.getElementById('modules').removeChild(module);
    nb_module+=-1;
    document.getElementById('nb_module').setAttribute("value",nb_module);
  }
}

// create a module in the form
function createModule(){
  nb_module+=1;
  var nbMod=document.getElementById('nb_module').setAttribute("value",nb_module);
  var modules= document.getElementById('modules');
  var new_module= document.createElement('div');
  new_module.setAttribute('id','module'+nb_module);

  var legend=document.createElement("legend");
  legend.innerHTML="Module "+nb_module+" :";
  new_module.appendChild(legend);

  var labelModule= document.createElement("label");
  labelModule.setAttribute('for','id_module_'+nb_module);
  labelModule.innerHTML="Module "+nb_module+" :";

  var labelMedia=document.createElement('label');
  labelMedia.setAttribute('for','id_module_'+nb_module);
  labelMedia.innerHTML="Media "+nb_module+" :";

  var inputModule=document.createElement('input');
  inputModule.setAttribute('id','id_module_'+nb_module);
  inputModule.setAttribute('name','module_'+nb_module);
  inputModule.setAttribute('type','file');

  var inputMedia=document.createElement('input');
  inputMedia.setAttribute('id','id_media_'+nb_module);
  inputMedia.setAttribute('name','media_'+nb_module);
  inputMedia.setAttribute('type','file');

  var p1=document.createElement('p');
  var p2=document.createElement('p');

  p1.appendChild(labelModule);
  p1.appendChild(inputModule);
  new_module.appendChild(p1);
  p2.appendChild(labelMedia);
  p2.appendChild(inputMedia);
  new_module.appendChild(p2);

  modules.appendChild(new_module);

  //var txt= document.createTextNode("{{formMod.as_p}}");
  //doc.appendChild(txt);
}
