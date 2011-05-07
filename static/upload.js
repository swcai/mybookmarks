(function() {
 var kMinImageSize = 30;
 var kOutlineColor = "#1030cc";
 var kOutlineSize = 3;
 var kShadowSize = 7;
 var gAvailableImages = [];

 // Create the share dialog in the corner of the window
 var container = div();
 container.id = "ff__container";
 container.style.backgroundColor = "black";
 container.style.position = "absolute";
 container.style.top = scrollPos().y + "px";
 container.style.right = "0";
 container.style.width = "auto";
 container.style.zIndex = 100000;
 container.innerHTML = '<html><p>Add to list successfully!</p></html>';
 document.body.appendChild(container);

 setTimeout(removeContainer, 3000);

 var i = document.createElement('img');
 i.src = document.location.protocol+'//localhost:8888/upload?title='+encodeURIComponent(document.title)+'&url='+encodeURIComponent(document.location.href);
 document.body.appendChild(i);

 function scrollPos() {
	 if (self.pageYOffset !== undefined) {
		 return { x: self.pageXOffset, y: self.pageYOffset };
	 }
	 var d = document.documentElement;
	 return { x: d.scrollLeft, y: d.scrollTop };
 }
 function setOpacity(element, opacity) {
	 if (navigator.userAgent.indexOf("MSIE") != -1) {
		 var normalized = Math.round(opacity * 100);
		 element.style.filter = "alpha(opacity=" + normalized + ")";
	 } else {
		 element.style.opacity = opacity;
	 }
 }
 function div(opt_parent) {
	 var e = document.createElement("div");
	 e.style.padding = "0";
	 e.style.margin = "0";
	 e.style.border = "0";
	 e.style.position = "relative";
	 if (opt_parent) {
		 opt_parent.appendChild(e);
	 }
	 return e;
 }
 function removeContainer() {
	 document.body.removeChild(byId('ff__container'));
 }
 function byId(id) {
	 return document.getElementById(id);
 }
})();
