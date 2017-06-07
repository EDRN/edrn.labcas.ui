var combos; //Variable containing combinations of radio buttons, needs to be initialzed in calling script

//Disable all radio buttons that are siblings to the radbio button with values in the list
function disable_siblings(list){
    if(list.length > 0){
        current_rad = $(":radio[value="+list[0]+"]");
        $("input[type=radio][name='" + current_rad.attr('name') + "']").each(function() {
            if(list.indexOf($(this).val()) == -1){
                $(this).attr('disabled',true);
                $(this).prop('checked', false);
                $(this).closest('label').css("color", "#F5F5F5");
            }else{
                //alert("enabled");
                $(this).attr('disabled',false);
                $(this).closest('label').css("color", "#000000");
            }
        });
    }
}

$( document ).ready(function() {
    //Any input radio button clicked will trigger to check if combinations are correct
    $("input:radio").click(function() {
        var available_list = [];
        if(combos.hasOwnProperty($(this).val())){
            for(var k in combos[$(this).val()]) available_list.push(combos[$(this).val()][k]);
            disable_siblings(available_list);
        }
    });
});
