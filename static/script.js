window.onload=function(){
  document.getElementById("Op1").addEventListener("click", op1);
  document.getElementById("Op2").addEventListener("click", op2);
  document.getElementById("Op3").addEventListener("click", op3);
  document.getElementById("Op4").addEventListener("click", op4);
  document.getElementById("Op5").addEventListener("click", op5);
  document.getElementById("vote-btn").addEventListener("click", submitVote);
  var candidate_list = document.getElementsByClassName("candidate");
  var i;
  for(i = 0; i < candidate_list.length; i++){
    candidate_list[i].addEventListener("mousedown", clearCandidate);
  }
}

function getFileInfo(){
    // Code taken from https://stackoverflow.com/questions/857618/javascript-how-to-extract-filename-from-a-file-input-control
    var fullPath = document.getElementById("vote-key-file").value;
    if (fullPath) {
        var startIndex = (fullPath.indexOf('\\') >= 0 ? fullPath.lastIndexOf('\\') : fullPath.lastIndexOf('/'));
        var filename = fullPath.substring(startIndex);
        if (filename.indexOf('\\') === 0 || filename.indexOf('/') === 0) {
            filename = filename.substring(1);
        }
        var textlabel = document.getElementById("file-label");
        textlabel.textContent = filename;
    }
}

function clearCandidate(){
  console.log("Candidates Cleared");
  var active_element = document.getElementsByClassName("active")[0];
  if(active_element){
    active_element.classList.remove("active");
  }
}

function op1(){
   document.getElementById("Op1").classList.add("active");
}

function op2(){
  document.getElementById("Op2").classList.add("active");
}

function op3(){
  document.getElementById("Op3").classList.add("active");
}

function op4(){
  document.getElementById("Op4").classList.add("active");
}

function op5(){
  document.getElementById("Op5").classList.add("active");
}

function submitVote(){
  var id = document.getElementById("voting-id").value;
  var code = document.getElementById("vote-key-file").value;
  if(code != "fail"){
    console.log("Vote submitted with code:  " + code);
    window.location.href = 'https://www.youtube.com/watch?v=FTQbiNvZqaY';
  }else{
    alert("Invalid code!");
  }
}
