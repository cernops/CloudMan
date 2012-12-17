$(document).ready(function()
	{
		// Set specific variable to represent all iframe tags.
		var iFrames = document.getElementsByTagName('iframe');

		// Resize heights.
		function iResize()
		{
			// Iterate through all iframes in the page.
			for (var i = 0, j = iFrames.length; i < j; i++)
			{
				// Set inline style to equal the body height of the iframed content.
				//iFrames[i].style.height = iFrames[i].contentWindow.document.body.offsetHeight + 'px';
                                frameTotHeight = 0;
                                try{
                                   frameTotHeight = iFrames[i].contentWindow.document.body.scrollHeight;
                                }catch(err){
                                }
                                //this.offsetTop = 0 + "px";
                                if (frameTotHeight <= 10){
                                    var height = document.documentElement.clientHeight;
                                    height -= iFrames[i].offsetTop;
                                    height -= 20;
                                    iFrames[i].style.height = height +"px";
                                 }else{
                                    iFrames[i].style.height = frameTotHeight + 40 + "px";
                                 }
			}
		}

		// Check if browser is Safari or Opera.
		if ($.browser.safari || $.browser.opera)
		{
			// Start timer when loaded.
			$('iframe').load(function()
				{
					setTimeout(iResize, 0);
				}
			);

			// Safari and Opera need a kick-start.
			for (var i = 0, j = iFrames.length; i < j; i++)
			{
				var iSource = iFrames[i].src;
				iFrames[i].src = '';
				iFrames[i].src = iSource;
			}
		}
		else
		{
			// For other good browsers.
			$('iframe').load(function()
				{
					// Set inline style to equal the body height of the iframed content.
					//this.style.height = this.contentWindow.document.body.offsetHeight + 'px';
                                        frameTotHeight = 0;
				        try{
					  frameTotHeight = this.contentWindow.document.body.scrollHeight;
					}catch(err){
					}
				        //this.offsetTop = 0 + "px";
				        if (frameTotHeight <= 10){
					   var height = document.documentElement.clientHeight;
				           height -= this.offsetTop;
					   height -= 20;
					   this.style.height = height +"px";
					}else{
					   this.style.height = frameTotHeight + 40 + "px";
					}
				}
			);
		}
	}
);
