$(document).ready(function(){
    $(".item-active").css('borderBottom',"solid 1px #ff7c08");
});
//判断页面是否有弹出
function menu_select(menu){
    var m = $(menu).attr('class');
    if (m=='Type') {
        $('.Sort-eject').removeClass('grade-w-roll');
    }
    else {
        $('.Type-eject').removeClass('grade-w-roll');
    }
    if ($('.'+m+'-eject').hasClass('grade-w-roll')) {
        $('.'+m+'-eject').removeClass('grade-w-roll');
    } else {
        $('.'+m+'-eject').addClass('grade-w-roll');
    }
}

//js点击事件监听开始
function item_select(sbj){
    $(sbj).siblings('li').css('borderBottom',"");
    $(sbj).css('borderBottom',"solid 1px #ff7c08");
    var value = $(sbj).attr('value');
    $(sbj).siblings('input').val(value);
    $(sbj).parent().parent().removeClass('grade-w-roll');
    loadmore(0, '');
}
