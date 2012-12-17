function getElement(aID){
    return (document.getElementById) ?
    document.getElementById(aID) : document.all[aID];
}

function getIFrameDocument(aID){
    var rv = null;
    var frame=getElement(aID);
    // if contentDocument exists, W3C compliant (e.g. Mozilla)
    if (frame.contentDocument)
       rv = frame.contentDocument;
    else // bad Internet Explorer  ;)
       rv = document.frames[aID].document;
    return rv;
}

function getAbsolutePos(el) {
    var r = {
        x: el.offsetLeft,
        y: el.offsetTop
    };
    if (el.offsetParent) {
        var tmp = getAbsolutePos(el.offsetParent);
        r.x += tmp.x;
        r.y += tmp.y;
    }
    return r;
}

function ShowToolTip(divId){
    getElement(divId).style.display="block";
    var p = getAbsolutePos(getElement(divId));
    return true;
}

function HideToolTip(divId){
    getElement(divId).style.display="none";
    return true;
}

function addLoadEvent(func) {
  var oldonload = window.onload;
  if (typeof window.onload != 'function') {
    window.onload = func;
  } else {
    window.onload = function() {
      oldonload();
      func();
    }
  }
}

function prepareInputsForHints() {
	var inputs = document.getElementsByTagName("input");
	for (var i=0; i<inputs.length; i++){
		// test to see if the hint span exists first
		if (inputs[i].parentNode.getElementsByTagName("span")[0]) {
			// the span exists!  on focus, show the hint
			inputs[i].onfocus = function () {
				this.parentNode.getElementsByTagName("span")[0].style.display = "inline";
			}
			// when the cursor moves away from the field, hide the hint
			inputs[i].onblur = function () {
				this.parentNode.getElementsByTagName("span")[0].style.display = "none";
			}
		}
	}
	// repeat the same tests as above for selects
	var selects = document.getElementsByTagName("select");
	for (var k=0; k<selects.length; k++){
		if (selects[k].parentNode.getElementsByTagName("span")[0]) {
			selects[k].onfocus = function () {
				this.parentNode.getElementsByTagName("span")[0].style.display = "inline";
			}
			selects[k].onblur = function () {
				this.parentNode.getElementsByTagName("span")[0].style.display = "none";
			}
		}
	}
}

//addLoadEvent(prepareInputsForHints);

/*var childCount = 0;
var newChildHandles = new Array();
function openNewWinLinkUrl(urlLink){
    var currDate = new Date();
    var winName = "";
    winName += currDate.getHours();
    winName += currDate.getMinutes();
    winName += currDate.getSeconds();
    newChildHandles[childCount] = window.open(urlLink, winName, 'height=600,width=850,resizable=yes,scrollbars=yes');
    childCount++;
}*/

function openNewWinLinkUrl(urlLink){
    parent.dataframe.location.href = urlLink;
}

function isEmpty(obj) { 
    for(var i in obj) {
       return false; 
    }
    return true; 
}

function is_int(value){
    if (value == ''){
	return false;
    }
    for (i = 0 ; i < value.length ; i++) {
        if ((value.charAt(i) < '0') || (value.charAt(i) > '9')) return false
    }
    return true;
}

function is_positive_float(value){
    if (value == ''){
	return false;
    }
    var charFilters = /^((\d+(\.\d*)?)|((\d*\.)?\d+))$/;
    if (charFilters.test(value))
       return true;
    else
       return false;
}

function round_float(x,n){
    if (x == 0){
        return 0.0;
    }
    if(!parseInt(n, 10))
        var n=0;
    if(!parseFloat(x))
        return false;
    return Math.round(x*Math.pow(10,n))/Math.pow(10,n);
}

// Removes leading whitespaces
function LTrim( value ) {
    var re = /\s*((\S+\s*)*)/;
    return value.replace(re, "$1");
}

// Removes ending whitespaces
function RTrim( value ) {
    var re = /((\s*\S+)*)\s*/;
    return value.replace(re, "$1");
}

// Removes leading and ending whitespaces
function trim( value ) {
    return LTrim(RTrim(value));
}

function resizeIframeOld(frameId) {
    var height = document.documentElement.clientHeight;
    height -= getElement(frameId).offsetTop;
    height -= 20;
    getElement(frameId).style.height = height +"px";
}

function resizeIframe(frameId){
    frameTotHeight = 0;
    try{
       frameTotHeight = getElement(frameId).contentWindow.document.body.scrollHeight;
    }catch(err){
    }
    getElement(frameId).offsetTop = 0 + "px";
    if (frameTotHeight <= 10){
       var height = document.documentElement.clientHeight;
       height -= getElement(frameId).offsetTop;
       height -= 20;
       getElement(frameId).style.height = height +"px";
    }else{
       getElement(frameId).style.height = frameTotHeight + 40 + "px";
    }
}
// ----------------------------------------------------------------------------
// AddClassName
//
// Description : adds a class to the class attribute of a DOM element
//    built with the understanding that there may be multiple classes
//
// Arguments:
//    objElement              - element to manipulate
//    strClass                - class name to add
//
function AddClassName(objElement, strClass, blnMayAlreadyExist){
   // if there is a class
   if ( objElement.className ){
      // the classes are just a space separated list, so first get the list
      var arrList = objElement.className.split(' ');
      // if the new class name may already exist in list
      if ( blnMayAlreadyExist ){
         // get uppercase class for comparison purposes
         var strClassUpper = strClass.toUpperCase();
         // find all instances and remove them
         for ( var i = 0; i < arrList.length; i++ ){
            // if class found
            if ( arrList[i].toUpperCase() == strClassUpper ){
               // remove array item
               arrList.splice(i, 1);
               // decrement loop counter as we have adjusted the array's contents
               i--;
             }
          }
      }
      // add the new class to end of list
      arrList[arrList.length] = strClass;

      // add the new class to beginning of list
      //arrList.splice(0, 0, strClass);
      
      // assign modified class name attribute
      objElement.className = arrList.join(' ');

    }else { // if there was no class
      // assign modified class name attribute      
      objElement.className = strClass;
    }
}

// ----------------------------------------------------------------------------
// RemoveClassName
//
// Description : removes a class from the class attribute of a DOM element
//    built with the understanding that there may be multiple classes
//
// Arguments:
//    objElement              - element to manipulate
//    strClass                - class name to remove
//
function RemoveClassName(objElement, strClass){
   // if there is a class
   if ( objElement.className ){
      // the classes are just a space separated list, so first get the list
      var arrList = objElement.className.split(' ');
      // get uppercase class for comparison purposes
      var strClassUpper = strClass.toUpperCase();
      // find all instances and remove them
      for ( var i = 0; i < arrList.length; i++ ){
         // if class found
         if ( arrList[i].toUpperCase() == strClassUpper ){
            // remove array item
            arrList.splice(i, 1);
            // decrement loop counter as we have adjusted the array's contents
            i--;
          }
      }
      // assign modified class name attribute
      objElement.className = arrList.join(' ');
   }
   // if there was no class
   // there is nothing to remove
}

function loadSplitter(){
   $("#MySplitter").splitter({
      type: "h",
      sizeTop: true,    
      accessKey: "P",
   });
   getElement("TopPane").style.height = 400 + 'px';
   getElement("BottomPane").style.height = 250 + 'px';
   $("#MySplitter").trigger("resize", [ 400 ]);
}
