document.getElementById('keluar').onclick = function(){
    location.href = "/logout";
};

function goto_home(){
    location.href = "/dashboard";
}

function goto_clientlist(){
    // goto init to populate database then go to clientlist
    location.href = "/init/0"
}

// ---------- dynamic page change ----------

// display show side nav button for mobile
let showSideNav = false;
document.getElementById('side-nav-show-button').onclick = function(){
    document.getElementById('side-navigation').style.display = 'flex';
    showSideNav = true;
}

document.getElementById('side-nav-hide-button').onclick = function(){
    document.getElementById('side-navigation').style.display = 'none';
    showSideNav = false;
}