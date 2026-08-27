function startInlineEdit(field) {
  document.querySelectorAll('.inline-edit-form.editing').forEach(function (f) {
    if (f.id !== field + 'EditForm') f.classList.remove('editing');
  });
  var form = document.getElementById(field + 'EditForm');
  form.classList.add('editing');
  var input = document.getElementById(field + 'Input');
  input.focus();
  if (input.select) input.select();
}

function handleInlineBlur(input) {
  if (input.value.trim() === input.defaultValue.trim()) {
    input.closest('.inline-edit-form').classList.remove('editing');
  } else {
    input.form.submit();
  }
}

function handleInlineKeydown(e, input) {
  if (e.key === 'Enter' && input.tagName === 'INPUT') {
    e.preventDefault();
    input.blur();
  } else if (e.key === 'Escape') {
    input.value = input.defaultValue;
    input.blur();
  }
}


function handleRowClick(e, href) {
  if (e.target.closest('.dropdown') || e.target.closest('a')) return;
  window.location = href;
}

(function () {
  var dropzone = document.getElementById('dropzone');
  if (!dropzone) return;

  var fileInput = document.getElementById('fileInput');
  var queueList = document.getElementById('queueList');
  var queueEmpty = document.getElementById('queueEmpty');
  var queueCount = document.getElementById('queueCount');
  var queuePlural = document.getElementById('queuePlural');

  function humanSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    var units = ['KB', 'MB', 'GB'];
    var val = bytes;
    for (var i = 0; i < units.length; i++) {
      val /= 1024;
      if (val < 1024 || i === units.length - 1) return val.toFixed(1) + ' ' + units[i];
    }
  }

  function renderQueue() {
    var files = fileInput.files;
    queueList.innerHTML = '';
    if (!files || files.length === 0) {
      queueList.appendChild(queueEmpty);
      queueCount.textContent = '0';
      queuePlural.textContent = 's';
      return;
    }
    queueCount.textContent = files.length;
    queuePlural.textContent = files.length === 1 ? '' : 's';
    for (var i = 0; i < files.length; i++) {
      var row = document.createElement('div');
      row.className = 'queue-row';
      row.innerHTML =
        '<span class="queue-name">' + files[i].name + '</span>' +
        '<span class="queue-size">' + humanSize(files[i].size) + '</span>' +
        '<span class="queue-status">Ready</span>';
      queueList.appendChild(row);
    }
  }

  fileInput.addEventListener('change', renderQueue);

  ['dragenter', 'dragover'].forEach(function (evt) {
    dropzone.addEventListener(evt, function (e) {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });
  });
  ['dragleave', 'drop'].forEach(function (evt) {
    dropzone.addEventListener(evt, function (e) {
      e.preventDefault();
      dropzone.classList.remove('dragover');
    });
  });
})();
