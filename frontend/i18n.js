export const STRINGS = {
  en: {
    heroTitle: "PDF to Word, with a quality report you can check",
    heroLead: "Choose Editable Word for clean text and real tables, or Maximum Layout Preservation to stay as close to the PDF page as possible. Scanned pages can be read with OCR.",
    tick1: "Real tables and images in Word", tick2: "OCR for scanned PDFs (English / Bangla when installed)", tick3: "Files are deleted automatically after a short time",
    convTitle: "Convert a PDF", dropTitle: "Drop your PDF here or click to browse", dropHint: "PDF only, up to {mb} MB",
    remove: "Remove", modeLegend: "Conversion mode", modeEditable: "Editable Word", modeEditableDesc: "Real paragraphs, headings, tables and pictures. Best for editing.",
    modePreserve: "Maximum Layout Preservation", modePreserveDesc: "Rebuilds positions, columns and fonts as closely as possible. Best for look-alike.",
    ocrLabel: "OCR for scanned pages", convert: "Convert to Word", download: "Download .docx", checksTitle: "Automated checks", notesTitle: "Notes for review",
    again: "Convert another", deleteNow: "Delete from server now",
    cmpTitle: "Which mode should I choose?", cmpEditable: "Text becomes normal Word paragraphs and headings, tables become Word tables, and pictures are placed inline. Page size and margins follow the PDF. Complex layouts (text boxes, overlapping items, vector charts) are simplified.",
    cmpPreserve: "Uses a layout-reconstruction engine to keep positions, columns, fonts, tables and images close to the original page. The result is closer to the PDF but can contain positioned text blocks that are harder to edit.",
    honestTitle: "What to expect", honestBody: "No PDF converter can promise identical formatting for every file, because PDF stores drawing instructions, not a flowing document. Rudrix compares the result against your PDF and tells you what it could and could not verify. Always glance through the Word file before sending it on.",
    footerNote: "Open-source engines: PyMuPDF, pdf2docx, python-docx, Tesseract",
    serverOk: "Server online", serverBad: "Server offline", serverWait: "Connecting…",
    ocrUnavailable: "OCR is not installed on this server, so scanned pages will be inserted as images.", ocrReady: "OCR ready: {langs}.",
    ocrNoBangla: " Bangla OCR data is not installed on this server.",
    uploading: "Uploading… {pct}%", processing: "Converting and checking the result…",
    errNoFile: "Please choose a PDF file.", errNotPdf: "Only PDF files are accepted.", errEmpty: "This file is empty.", errTooLarge: "File is larger than {mb} MB.",
    errNetwork: "Could not reach the conversion server. Check your connection or the API URL.", errGeneric: "Conversion failed. Please try again.", errTimeout: "The request took too long.",
    configMissing: "API URL is not configured. Edit config.js (or set RUDRIX_API_URL when building).",
    levelgood: "Checks passed", levelreview: "Needs review", levellow: "Check carefully",
    st_pass: "OK", st_warn: "Review", st_fail: "Problem", st_skip: "Not checked",
    c_text_coverage: "Text coverage", c_extra_text: "Extra text", c_images: "Images", c_tables: "Tables", c_page_count: "Page count",
    deleted: "File deleted from the server.", expires: "Download available for about {min} min."
  },
  bn: {
    heroTitle: "PDF থেকে Word, সাথে যাচাইযোগ্য কোয়ালিটি রিপোর্ট",
    heroLead: "পরিষ্কার টেক্সট ও আসল টেবিলের জন্য Editable Word, আর PDF পাতার সবচেয়ে কাছাকাছি লেআউটের জন্য Maximum Layout Preservation বেছে নিন। স্ক্যান করা পাতা OCR দিয়ে পড়া যায়।",
    tick1: "Word-এ আসল টেবিল ও ছবি", tick2: "স্ক্যান PDF-এর জন্য OCR (ইংরেজি / বাংলা, ইনস্টল থাকলে)", tick3: "ফাইল অল্প সময় পর নিজে থেকেই মুছে যায়",
    convTitle: "PDF কনভার্ট করুন", dropTitle: "এখানে PDF ছেড়ে দিন অথবা ক্লিক করে বাছুন", dropHint: "শুধু PDF, সর্বোচ্চ {mb} MB",
    remove: "সরান", modeLegend: "কনভার্সন মোড", modeEditable: "Editable Word", modeEditableDesc: "আসল প্যারাগ্রাফ, হেডিং, টেবিল ও ছবি। এডিট করার জন্য সেরা।",
    modePreserve: "Maximum Layout Preservation", modePreserveDesc: "অবস্থান, কলাম ও ফন্ট যতটা সম্ভব হুবহু রাখার চেষ্টা। দেখতে একরকম রাখার জন্য সেরা।",
    ocrLabel: "স্ক্যান পাতার জন্য OCR", convert: "Word-এ কনভার্ট করুন", download: ".docx ডাউনলোড", checksTitle: "স্বয়ংক্রিয় যাচাই", notesTitle: "পর্যালোচনার নোট",
    again: "আরেকটি কনভার্ট করুন", deleteNow: "এখনই সার্ভার থেকে মুছুন",
    cmpTitle: "কোন মোড বেছে নেবেন?", cmpEditable: "টেক্সট সাধারণ Word প্যারাগ্রাফ ও হেডিং হয়, টেবিল Word টেবিল হয়, ছবি লাইনের মধ্যে বসে। পাতার আকার ও মার্জিন PDF-এর মতো থাকে। জটিল লেআউট (টেক্সট বক্স, ওভারল্যাপ, ভেক্টর চার্ট) সরল হয়ে যেতে পারে।",
    cmpPreserve: "লেআউট-পুনর্গঠন ইঞ্জিন দিয়ে অবস্থান, কলাম, ফন্ট, টেবিল ও ছবি মূল পাতার কাছাকাছি রাখা হয়। ফল PDF-এর বেশি কাছাকাছি হয়, তবে নির্দিষ্ট জায়গায় বসানো টেক্সট ব্লক থাকতে পারে যা এডিট করা কঠিন।",
    honestTitle: "কী আশা করবেন", honestBody: "কোনো PDF কনভার্টারই প্রতিটি ফাইলের জন্য হুবহু ফরম্যাটের নিশ্চয়তা দিতে পারে না, কারণ PDF-এ থাকে আঁকার নির্দেশ, প্রবাহমান ডকুমেন্ট নয়। Rudrix ফলাফলটি আপনার PDF-এর সাথে মিলিয়ে দেখে এবং কী যাচাই করতে পারল ও পারল না তা জানায়। পাঠানোর আগে Word ফাইলটি একবার দেখে নিন।",
    footerNote: "ওপেন-সোর্স ইঞ্জিন: PyMuPDF, pdf2docx, python-docx, Tesseract",
    serverOk: "সার্ভার চালু", serverBad: "সার্ভার বন্ধ", serverWait: "সংযোগ হচ্ছে…",
    ocrUnavailable: "এই সার্ভারে OCR ইনস্টল নেই, তাই স্ক্যান পাতা ছবি হিসেবে বসবে।", ocrReady: "OCR প্রস্তুত: {langs}।",
    ocrNoBangla: " এই সার্ভারে বাংলা OCR ডেটা ইনস্টল নেই।",
    uploading: "আপলোড হচ্ছে… {pct}%", processing: "কনভার্ট ও ফলাফল যাচাই হচ্ছে…",
    errNoFile: "অনুগ্রহ করে একটি PDF ফাইল বাছুন।", errNotPdf: "শুধু PDF ফাইল গ্রহণযোগ্য।", errEmpty: "ফাইলটি খালি।", errTooLarge: "ফাইল {mb} MB-এর বেশি।",
    errNetwork: "কনভার্সন সার্ভারে পৌঁছানো যায়নি। সংযোগ বা API URL দেখুন।", errGeneric: "কনভার্সন ব্যর্থ হয়েছে। আবার চেষ্টা করুন।", errTimeout: "অনুরোধ অনেক সময় নিয়েছে।",
    configMissing: "API URL সেট করা নেই। config.js সম্পাদনা করুন (অথবা বিল্ডের সময় RUDRIX_API_URL দিন)।",
    levelgood: "যাচাই সফল", levelreview: "পর্যালোচনা দরকার", levellow: "সতর্কভাবে দেখুন",
    st_pass: "ঠিক আছে", st_warn: "দেখুন", st_fail: "সমস্যা", st_skip: "যাচাই হয়নি",
    c_text_coverage: "টেক্সট কভারেজ", c_extra_text: "বাড়তি টেক্সট", c_images: "ছবি", c_tables: "টেবিল", c_page_count: "পাতার সংখ্যা",
    deleted: "সার্ভার থেকে ফাইল মুছে ফেলা হয়েছে।", expires: "প্রায় {min} মিনিট ডাউনলোড করা যাবে।"
  }
};

export function t(lang, key, params = {}) {
  const s = (STRINGS[lang] && STRINGS[lang][key]) ?? STRINGS.en[key] ?? key;
  return s.replace(/\{(\w+)\}/g, (_, k) => (k in params ? params[k] : `{${k}}`));
}
