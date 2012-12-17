// Functions used for cloudman portal functionalities

function validateResourceParameters(hepSpec, memory, storage, bandwidth){
    if ( (hepSpec == '') && (storage == '') ){
       return ('One or both Hepspec and Storage value, if entered, should be provided with a positive value (greater than 0)');
    }
    if (hepSpec != ''){
       if (!is_positive_float(hepSpec)){
          return ('One or both Hepspec and Storage value, if entered, should have a positive float value (greater than 0)');
       }
    }
    if (memory != ''){
       if (!is_positive_float(memory)){
          return ('Memory value can be empty or a positive float value (greater than or equal to 0)');
       }
    }
    if (storage != ''){
       if (!is_positive_float(storage)){
          return ('One or both Hepspec and Storage value, if entered, should have a positive float value (greater than 0)');
       }
    }
    if (bandwidth != ''){
       if (!is_positive_float(bandwidth)){
          return ('Bandwidth value can be empty or a positive float value (greater than or equal to 0)');
       }
    }
    if ( (hepSpec == '') && (storage != '') ){
       if (parseFloat(storage, 10) <= 0){
          return ('Hepspec and/or Storage value if entered, should be provided with a positive value (greater than 0)');
       }
    }else if ( (hepSpec != '') && (storage == '') ){
       if (parseFloat(hepSpec, 10) <= 0){
          return ('Hepspec and/or Storage value if entered, should be provided with a positive value (greater than 0)');
       }
    }else{
       if ( (parseFloat(hepSpec, 10) <= 0) && (parseFloat(storage, 10) <= 0) ){
          return ('One or both Hepspec and Storage value, if entered, should be provided with a positive value (greater than 0)');
       }
    }
    return '';
}

function checkNumberParameterChange(oldValue, newValue){
   valueChanged = false;
   if (oldValue != newValue){
      if ( ((oldValue != '') && (newValue == ''))
        || ((oldValue == '') && (newValue != '')) ){
        valueChanged = true
      }else{
        if (parseFloat(oldValue, 10) != parseFloat(newValue, 10)){
           valueChanged = true;
        } 
      }
   }
   return valueChanged;
}
