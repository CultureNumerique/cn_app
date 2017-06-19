
var url_base="p/";
var url_export="/export/txt";

var list_url=[];
var nb_module=1;
var apercu_visible=true;

// Send an url in the iframe which generate the preview
function convertir_home(url_base,home_url)
{
  var url=url_base+'apercu_home/'+home_url;
  var frame=document.getElementById("frametest");

  frame.setAttribute("src",url);
}

function convertir_module(url_base,module_url,feedback)
{
	if (feedback) feedback="1"
	else feedback="0"
  var url=url_base+'apercu_module/'+module_url+'/'+feedback;
  var frame=document.getElementById("frametest");

  frame.setAttribute("src",url);
}

// Generate a random string of nb_char characters
function random_string(nb_char)
{
  var list = new Array("a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z","0","1","2","3","4","5","6","7","8","9");
  var res ="";
  for(i = 0; i < nb_char; i++)
    res = res + list[Math.floor(Math.random()*list.length)];
  return res;
}

//Generate a random link using url_base and a definite number of random char
//The results is inserted into list_url
function generate_link(etherpad_url, nb_char, is_module){
  rand=random_string(nb_char);
  if(is_module){
    rand="module-"+rand;
  }
  else{
    rand="home-"+rand;
  }

	url=etherpad_url+url_base+rand;
	list_url.push(rand);
	return url;
}

//set a link using nb_char random char to a definite iframe (using id)
function give_link_to_iframe(etherpad_url, idFrame, idInput, nb_char, is_module){
	var frame = document.getElementById(idFrame);
	var input = document.getElementById(idInput);
	var link=""
	if(nb_module+1<=list_url.length){
		link = etherpad_url+url_base+list_url[nb_module];
	}
	else{
		link = generate_link(etherpad_url, nb_char, is_module);
	}
	frame.setAttribute("src",link);
	input.setAttribute("value",link+url_export);

}


function afficher_apercu(){
	var frameHome=document.getElementById("framehome");
	var frameTest=document.getElementById("frametest");
	if(apercu_visible) {
		apercu_visible=false;
		frameHome.setAttribute("width","90%");
		frameTest.setAttribute("width","0%");
	}
	else {
		apercu_visible=true;
		frameHome.setAttribute("width","45%");
		frameTest.setAttribute("width","45%");
	}

}
