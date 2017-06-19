

function process(){

  //get the different img elements
  res=document.getElementsByTagName('img');

  //for each url from img
  for(var i=0; i<res.length; i++){
    var value = res[i].getAttribute('src');
    //img is not a http link
    if(!value.includes('http')){
      res[i].setAttribute('src','/static/img/logo_cercle_vert.png');
    }
  }
}
