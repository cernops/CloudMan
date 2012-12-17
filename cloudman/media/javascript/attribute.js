function deleteAttribute(parent_div,child_div)
{
	var child = document.getElementById(child_div);
    var parent = document.getElementById(parent_div);
    parent.removeChild(child);
}

function addAttribute(divName,attr_name,attr_value)
{
	if (typeof  attr_name == "undefined")
		attr_name = '';
	if (typeof  attr_value == "undefined")
		attr_value = '';
	var newdiv = document.createElement('div');
    var uniqueid = (new Date()).getTime().toString();
    var div_id="div" + uniqueid;
    newdiv.setAttribute("id",div_id);
    //newdiv.innerHTML ="<table align=center><tr><td>Attribute Name:</td><td><input type='text' name='attribute_name' value='"+attr_name+"'></td>   <td>Attribute Value:</td><td><input type='text'  name='attribute_value' value='"+attr_value+"'></td> <td><a href='#' style='cursor: pointer' onClick=\"deleteAttribute('"+divName+"','" + div_id+ "');\"><img src='/media/images/remove.png' height='15px' width='15px' align='center' title='delete Attribute' border='0'/></a></td></tr></table>";
    newdiv.innerHTML = "<dl><dt>Attribute Name: <input type='text' name='attribute_name' value='"+attr_name+"'> </dt><dd>Attribute Value: <input type='text' name='attribute_value' value='"+attr_value+"'>&nbsp;&nbsp;<a href='#' style='border-top:0px;top:0px;cursor: pointer' onClick=\"deleteAttribute('"+divName+"','" + div_id+ "');\"><img src='/cloudman/media/images/remove.png' height='15px' width='15px' align='center' title='delete Attribute' border='0'/></a></dd></dl>";

    document.getElementById(divName).appendChild(newdiv);
}
