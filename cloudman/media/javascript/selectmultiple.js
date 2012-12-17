/*function Pager(tableName, itemsPerPage) 
{
    this.tableName = tableName;
    this.itemsPerPage = itemsPerPage;
    this.currentPage = 1;
    this.pages = 0;
    this.inited = false;
    this.showRecords = function(from, to) 
    					{       
        					var rows = document.getElementById(tableName).rows;
        					for (var i = 1; i < rows.length; i++)
        					{
            					if (i < from || i > to) 
								{
									rows[i].style.display = 'none';
 								}
 								else
                					rows[i].style.display = '';
        					}
$("tr[class=collapse]").hide();
    					}
    this.showPage = function(pageNumber) 
    					{
     						if (! this.inited) 
     						{
      							alert("not inited");
      							return;
     						}
							var oldPageAnchor = document.getElementById('pg'+this.currentPage);
							oldPageAnchor.className = 'pg-normal';
							this.currentPage = pageNumber;
							var newPageAnchor = document.getElementById('pg'+this.currentPage);
							newPageAnchor.className = 'pg-selected';
							var from = (pageNumber - 1) * itemsPerPage + 1;
							var to = from + itemsPerPage - 1;
							this.showRecords(from, to);
						}  
   
this.prev = function() 
				{
        			if (this.currentPage > 1)
            			this.showPage(this.currentPage - 1);
    			}

this.next = function() 
				{
        			if (this.currentPage < this.pages) 
        			{
            			this.showPage(this.currentPage + 1);
        			}
    			}                       
   
this.init = function()
				{
        			var rows = document.getElementById(tableName).rows;
        			var records = (rows.length - 1);
        			this.pages = Math.ceil(records / itemsPerPage);
        			this.inited = true;
    			}

this.showPageNav = function(pagerName, positionId) 
					{
     					if (! this.inited)
     					{
      						alert("not inited");
      						return;
     					}
     					var element = document.getElementById(positionId);
     					var pagerHtml = '<span onclick="' + pagerName + '.prev();" class="pg-normal"> &#171 Prev </span> | ';
        				for (var page = 1; page <= this.pages; page++)
            				pagerHtml += '<span id="pg' + page + '" class="pg-normal" onclick="' + pagerName + '.showPage(' + page + ');">' + page + '</span> | ';
        				pagerHtml += '<span onclick="'+pagerName+'.next();" class="pg-normal"> Next &#187;</span>';           
        				element.innerHTML = pagerHtml;
    				}
}
*/

function wordwrap( str)
{
	brk = '<br/>';
	width = 200;
	cut = true;
	if (!str) { return str; }
	var regex = '.{1,' +width+ '}(\\s|$)' + (cut ? '|.{' +width+ '}|.+$' : '|\\S+?(\\s|$)');
	var tmp = str.match( RegExp(regex, 'g') ).join( brk );	
	return tmp;
}


function checkThemAll(chk,formName,checkBoxName)
{
	var form = document.forms[formName];
    var noOfCheckBoxes = form[checkBoxName].length;
    if (noOfCheckBoxes == undefined)
	{
        if(chk.checked==true)
        {
            if(form[checkBoxName].checked==false)
                form[checkBoxName].checked=true;
        }
        else
        {
            if(form[checkBoxName].checked==true)
                form[checkBoxName].checked=false;
        }
	}	
	for(var x=0;x<noOfCheckBoxes;x++)
    {
    	if(chk.checked==true)
        {
        	if(form[checkBoxName][x].checked==false)
            {
            	form[checkBoxName][x].checked=true;
            }
        }
        else
        {
        	if(form[checkBoxName][x].checked==true)
            {
            	form[checkBoxName][x].checked=false;
            }
        }
    }
}

function submitForm(formName,checkBoxName,errorAlert,confirmAlert)
{
	var form = document.forms[formName];
    var noOfCheckBoxes = form[checkBoxName].length;
    var name_list = '';
    var selected = false;
    if (noOfCheckBoxes == undefined)
    {
        if(form[checkBoxName].checked==true)
        {
			name_list += form[checkBoxName].value +"%%"
			selected = true
        }
    }

    for(var x=0;x<noOfCheckBoxes;x++)
    {
    	if(form[checkBoxName][x].checked==true)
        {
        	name_list += form[checkBoxName][x].value + "%%"; // %% is used as seperator
            selected = true;
        }
    }
    if(!selected)
    {
    	alert(errorAlert);
        return false;
    }
    var name_listLen = name_list.length;
    name_list = name_list.slice(0,name_listLen - 2);
    document.getElementById('name_list').value = name_list;
    if(confirm(confirmAlert))
    {
    	var comment = prompt('Write comment','Deleting item')
		if(comment !=''  && comment !=null)
		{
    		var form = document.getElementById('dataForm');
    		var element = document.createElement('input');
			element.setAttribute("type", 'hidden');
    		element.setAttribute("value", comment);
    		element.setAttribute("name", 'comment');
    		form.appendChild(element);
    		document.dataForm.submit();
    	}
 	    	
    }
    else
        return false;
}

function searchTable(inputVal,tableid)
{
	var table = $(tableid);
	table.find('tr').each(function(index, row)
	{
		var allCells = $(row).find('td');
		if(allCells.length > 0)
		{
			var found = false;
			allCells.each(function(index, td)
			{
				var regExp = new RegExp(inputVal, 'i');
				if(regExp.test($(td).text()))
				{
					found = true;
					return false;
				}
			});
			if(found == true)
				$(row).show();
			else 
				$(row).hide();
		}
	});
}

function searchMultiTable(inputVal)
{
    var tableList = document.getElementsByTagName('table');
    for (var i = 0; i < tableList.length; i++) 
    {
        var table = tableList[i];
        tableid = table.id;
        searchTable(inputVal,'#'+tableid);
    }
}




function clearDefaultText(e) 
{
    var target = window.event ? window.event.srcElement : e ? e.target : null;
    if (!target) return;
    
    if (target.value == target.defaultText) {
        target.value = '';
    }
}

function replaceDefaultText(e) 
{
    var target = window.event ? window.event.srcElement : e ? e.target : null;
    if (!target) return;
    
    if (target.value == '' && target.defaultText) {
        target.value = target.defaultText;
    }
}

function addEvent(element, eventType, lamdaFunction, useCapture) {
    if (element.addEventListener) {
        element.addEventListener(eventType, lamdaFunction, useCapture);
        return true;
    } else if (element.attachEvent) {
        var r = element.attachEvent('on' + eventType, lamdaFunction);
        return r;
    } else {
        return false;
    }
}



	function showHideTableRow(tableid) 
	{
    	var table = document.getElementById(tableid);
		for (var i = 0, row; row = table.rows[i]; i++)
		{
			if(row.id == 'hidden')
			{
				if (row.style.display == '') 
					row.style.display = 'none';
				else 
					row.style.display = '';
   			}
      	}
  	}   

   function toggleTableList(togglebutton,tableid,category)
   {
   		if (togglebutton.value == 'Show ALL')
   		{
   			togglebutton.value='Hide Others';
   			togglebutton.title='Hide all '+category+' for which you are not authorized';
   		}
   		else
   		{
   			togglebutton.value='Show ALL';
			togglebutton.title='Show all '+category;
   		}
   		showHideTableRow(tableid);
   }




