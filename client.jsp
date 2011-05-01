javascript:function iprl5() {
 var d=document, z=d.createElement('scr'+'ipt'), b=d.body, l=d.location;
 try { 
    if (!b) 
        throw(0);
    d.title='(Saving...) ' + d.title;    
    z.setAttribute('src', l.protocol+'//localhost:8888/upload?title=' + encodeURIComponent(d.title) + '&url=' + encodeURIComponent(l.href));
    b.appendChild(z);
    } catch(e) {
        alert('Please wait until the page has loaded.');
    }
}
iprl5();
void(0)