document.documentElement.setAttribute('data-validation-js', 'loaded');

window.addEventListener('error', function(event) {
  document.documentElement.setAttribute('data-validation-error', String(event.message));
});

window.addEventListener('unhandledrejection', function(event) {
  document.documentElement.setAttribute('data-validation-error', String(event.reason));
});
