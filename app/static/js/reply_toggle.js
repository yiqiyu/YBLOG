$(document).ready(
	function() {
		$("a.btn").click(
			function(){
				replyToggle(this);
				return false;
			}
		)
	}
)
	

function replyToggle(that){
	if (!$('div.replyToggle').length){
		$(that).parent().append("<div class='replyToggle' style='display:none'></div>");
		Sijax.request('ajax_reply', [parseInt($(that).attr("id"))]);
		$('div.replyToggle').delay(100).slideDown("fast")
		}
	else {
		$('div.replyToggle').slideUp("fast", function(){$(this).remove()})
		}	
}