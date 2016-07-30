$(function() {
	$("a.btn").click(
		function(){
			replyToggle(this);
			return false;
		}
	);
})
	

function replyToggle(that){
	if (!$('div.replyToggle').length){
		$(that).parent().append("<div class='replyToggle' style='display:none'></div>");
		Sijax.request('ajax_reply', [+$(that).attr("id")], {'complete': function(){		
		    $('div.replyToggle')
		        //.delay(200)
			    .slideDown("fast", function(){
			        $('input[type="checkbox"]')[0].checked = true;
				    $('textarea').autosize();
			    })
			}});   
		}
	else {
		$('div.replyToggle').slideUp("fast", function(){$(this).remove()});
		}	
}

