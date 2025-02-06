function extractGiftCardCodes() {
  Logger.log('Starting extractGiftCardCodes function');
  
  // Search for emails from "gifts@gyftr.com" within the last 24 hours
  var threads = GmailApp.search('from:gifts@gyftr.com newer_than:1d');
  Logger.log('Found ' + threads.length + ' threads');

  var giftCardCodes = new Set();

  for (var i = 0; i < threads.length; i++) {
    var messages = threads[i].getMessages();
    Logger.log('Thread ' + (i + 1) + ': Found ' + messages.length + ' messages');

    for (var j = 0; j < messages.length; j++) {
      var subject = messages[j].getSubject();
      Logger.log('Message ' + (j + 1) + ': Subject - ' + subject);

      var body = messages[j].getBody();

      var codes = extractCodesFromBody(body);
      Logger.log('Message ' + (j + 1) + ': Found codes - ' + codes.join(', '));

      codes.forEach(code => giftCardCodes.add(code));
    }
  }

  Logger.log('Found gift card codes: ' + Array.from(giftCardCodes).join(', '));

  exportToSheet(Array.from(giftCardCodes));
}

function extractCodesFromBody(body) {
  var codes = [];
  var regex = /\b[A-Za-z0-9]{14}\b/g;
  var match;
  while ((match = regex.exec(body)) !== null) {
    // Validate if the code is alphanumeric and contains both letters and numbers
    if (/^[A-Za-z0-9]+$/.test(match[0]) && /[A-Za-z]/.test(match[0]) && /[0-9]/.test(match[0])) {
      codes.push(match[0]);
    }
  }
  return codes;
}

function exportToSheet(codes) {
  // Get the current date
  var now = new Date();
  
  // Format the date as YYYY-MM-DD
  var formattedDate = now.getFullYear() + '-' + 
                      ('0' + (now.getMonth() + 1)).slice(-2) + '-' + 
                      ('0' + now.getDate()).slice(-2);
  
  // Create the spreadsheet with the formatted date in the name
  var spreadsheetName = 'Gift_Card_Codes_' + formattedDate;
  var spreadsheet = SpreadsheetApp.create(spreadsheetName);
  var sheet = spreadsheet.getActiveSheet();
  sheet.appendRow(['Gift Card Codes']);
  codes.forEach(function(code) {
    sheet.appendRow([code]);
  });
  Logger.log('Gift card codes exported to Google Sheets: ' + spreadsheet.getUrl());
}