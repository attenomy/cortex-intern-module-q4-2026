CTX-002: Cognitive Document Entity Extractor & Layout Classifier
Module: api/modules/doc_extractor/
API endpoint: POST /api/v1/extract
Branch: feature/CTX-002-doc-extractor
Status: Core implementation and test evidence prepared; acceptance validation remains incomplete.
1. Problem Statement
The current document extraction module in api/modules/doc_extractor/
returns a mocked JSON response instead of performing actual document
processing.

It does not currently perform:
- Document image decoding and validation.
- Document layout classification.
- OCR-based text extraction.
- Structured invoice entity extraction.
- Strict validation of extracted financial information.
- Actual document-region bounding-box detection and evaluation.
The objective of CTX-002 is to replace the mocked implementation with a
real document-processing pipeline that supports document image
validation, four-class layout classification, OCR-based entity
extraction, spatial layout analysis, and structured response validation.

The implementation must not use hardcoded sample entities, fabricated
predictions, or silent fallback behaviour in place of actual model
inference.
2. Project Scope
2.1 In Scope
- Base64-encoded document image input.
- Defensive Base64 and image validation.
- Document type validation using a DocumentType enum.
- MobileNetV3-Small classification of exactly four document
  categories.
- OpenCV-based image preprocessing and spatial analysis.
- Tesseract OCR through pytesseract or a lightweight wrapper.
- OCR abstraction behind an interface so CI tests can use mocked
  fixtures without requiring OS-level OCR binaries.
- Invoice entity extraction.
- Pydantic-based request, entity, and response validation.
- Bounding-box detection for major document layout regions.
- FastAPI lifespan model initialization and warm-up.
- Fail-fast startup behaviour when model weights are missing or
  corrupted.
- Unit and integration testing, including negative and boundary cases.
- Dataset preparation and reproducible train/validation/test
  splitting.
- Performance and memory profiling.
2.2 Primary Evaluation Target
Invoices are the primary target for entity extraction evaluation.

The required invoice entities are:
- vendor_name
- invoice_number
- net_amount
- currency
The document classifier must support all four document categories, while
invoice entity extraction is the primary evaluated extraction task.
2.3 Confirmed Document Classes
MobileNetV3-Small must classify exactly these four categories:
1. invoice --- primary evaluation target.
2. receipt
3. contract
4. purchase_order
No additional classification categories are included in the CTX-002
classification target.
2.4 Dataset and Reproducibility
The confirmed datasets are:
- SROIE: invoice entity extraction.
- RVL-CDIP samples: four-class document layout classification.
The dataset split must be:

  Split                Percentage
  Training                    70%
Validation                  15%
Held-out testing            15%

The random seed must be fixed at 42.

The held-out test split must remain separate from training and
validation and must be used for final evaluation. Dataset preparation
must avoid leakage between the splits. The exact sample selection and
any filtering or mapping required to form the four confirmed classes
should be documented rather than assumed.
3. Functional Requirements
FR-01: Document Image Input
- The API must primarily accept Base64-encoded document images.
- The request must contain a document ID, document type, and Base64
  image content.
- Supported document types must be represented using a DocumentType
  enum with exactly these values:
  - invoice
  - receipt
  - contract
  - purchase_order
FR-02: Input Validation
- The system must validate incoming Base64 content before image
  processing.
- Malformed Base64 input must return HTTP 422.
- Base64 that decodes successfully but does not represent a supported
  image must return HTTP 422.
- Corrupted or truncated image data must be rejected safely with HTTP
  422.
- Empty document IDs must return HTTP 400.
- Whitespace-only document IDs must return HTTP 400.
- Whitespace-only image payloads must return HTTP 400.
- Oversized or invalid image inputs must be handled safely without an
  unhandled server error.
- Runtime payload validation failures must not be confused with
  model-startup failures.
FR-03: Document Classification and Image Processing
- The system must use torchvision.models.mobilenet_v3_small for
  document classification.
- Pretrained torchvision weights must be used as the starting point
  for the model.
- The final classification head must support exactly four classes:
  invoice, receipt, contract, and purchase_order.
- OpenCV may be used alongside MobileNetV3 for image preprocessing,
  contour detection, and spatial analysis.
- The pipeline must support identification of the major document
  layout regions specified in FR-07.
- Model predictions and evaluation metrics must be based on actual
  inference and held-out evaluation data; hardcoded predictions are
  not permitted.
FR-04: OCR and Entity Extraction
- The system must use Tesseract OCR through pytesseract or a
  lightweight wrapper.
- OCR functionality must be abstracted behind an interface so that the
  extraction pipeline is not tightly coupled to a specific OCR
  implementation.
- CI unit tests must be able to use mocked OCR fixtures and must not
  require external operating-system OCR binaries.
- Extracted OCR text must be processed to identify relevant document
  entities.
- OCR or text-decoding failures must be handled safely and reported
  through a structured error path.
- Missing optional fields must not cause the entire extraction process
  to fail.
FR-05: Invoice Entity Extraction
Invoices are the primary evaluation target.

The system must extract and validate the following invoice fields:

  Field              Expected Meaning
  vendor_name      Name of the vendor
invoice_number   Invoice identifier
net_amount       Invoice net amount
currency         Currency represented by an ISO-4217 code

The extraction pipeline must not fabricate values when a field cannot be
identified. Missing mandatory invoice fields must be represented as
extraction or validation failures rather than silently filled with
sample values.
FR-06: Entity Validation
- Extracted entities must be validated using Pydantic models.
- net_amount must be greater than 0.0.
- currency must be validated against ISO-4217 currency codes.
- Invalid financial values must not be silently accepted.
- The required invoice fields must be checked for presence and
  validity.
- Missing optional fields must be represented as null with low
  confidence, as specified in the ticket.
- Entity confidence scores must be retained for evaluation.
- Field confidence evaluation must be distinguished from layout-region
  IoU evaluation.
FR-07: Bounding-Box Detection and Evaluation
The bounding-box IoU target of at least 0.75 applies to these major
document layout regions:
1. Header
2. Line-Item Table
3. Totals Block
Requirements:
- The pipeline must compute bounding boxes for these major layout
  regions.
- Predicted region boxes must be compared with ground-truth boxes.
- IoU for the specified layout regions must be at least 0.75.
- Individual entity values, including vendor_name and net_amount,
  must be evaluated using schema validity and field confidence scores,
  not the layout-region IoU target.
FR-08: Model Lifecycle and Startup Behaviour
- Vision and OCR components must be initialized during FastAPI
  application startup using the lifespan mechanism.
- Model weights must be loaded during startup.
- Model warm-up must happen before the application accepts extraction
  requests.
- Models must not be loaded independently for every request.
- The application must fail fast during startup if model weights are
  missing or corrupted.
- Startup failures must be explicit; the application must not mask
  them with a fake model, hardcoded prediction, or silent fallback.
- Invalid individual document payloads received after startup must
  return HTTP 422.
FR-09: API Response
- The API must return a structured extraction response.
- The response must include the document ID, extracted fields, schema
  validation status, and extraction latency, consistent with the
  module's response contract.
- Invalid runtime inputs must return the specified HTTP error
  responses.
- Processing failures must not result in unhandled server errors.
- The response must not present mocked or fabricated values as actual
  extracted entities.
FR-10: Testing and Reliability
- The module must contain at least 12 unit and integration tests.
- More than 60% of the tests must cover negative and boundary cases.
- Tests must cover malformed Base64, corrupted image data, non-image
  payloads, empty identifiers, whitespace-only payloads, missing
  required invoice fields, invalid amounts, invalid currency, corrupt
  EXIF data, and extreme image aspect ratios.
- OCR-dependent CI tests must use mocked fixtures and must not require
  external Tesseract OS binaries.
- Startup tests must cover missing and corrupted model weights.
- The complete existing test suite must pass.
4. Performance and Evaluation Targets
  Metric                                      Target Evaluation Context
  Classification Macro                     >= 0.90 Held-out test split
F1                                                 

  Layout-region                            >= 0.75 Header, Line-Item
bounding-box IoU                                   Table, Totals Block

  Median CPU extraction                   < 150 ms CPU extraction
latency                                            pipeline

  CPU P95 extraction                      < 300 ms CPU extraction
latency                                            pipeline
Negative and boundary                      > 60% CTX-002 test suite
test ratio
Latency measurements must be obtained through reproducible profiling and
must identify the tested environment and measurement method. Do not
report target values as achieved results unless supported by actual
measurements.

Macro F1 must be calculated on the held-out test split. The final report
must state the class-wise results and the evaluation method used.
5. Confirmed Technical Decisions
The following decisions have been confirmed by the project mentor and
supersede the earlier pending questions.
5.1 OCR Engine
Use Tesseract through pytesseract or a lightweight wrapper. Keep it
behind an interface so CI unit tests can use mock fixtures without
requiring external OS binaries.
5.2 Classification Classes
MobileNetV3-Small must classify exactly four categories:
- invoice
- receipt
- contract
- purchase_order
5.3 Bounding-Box Evaluation Scope
The IoU target applies to the Header, Line-Item Table, and
Totals Block regions. Individual entity values such as vendor_name
and net_amount are evaluated through schema validity and field
confidence scores.
5.4 Dataset and Splits
Use SROIE for invoice entity extraction and RVL-CDIP samples for
four-class layout classification. Split the selected data into 70%
training, 15% validation, and 15% held-out testing, using seed 42.
5.5 Startup Failure Behaviour
Fail fast during application startup if model weights are missing or
corrupted. Do not use a fake fallback. Invalid individual runtime
payloads must return HTTP 422.
5.6 Classification Metric
The confirmed Macro F1 threshold is >= 0.90 on the held-out test
split.
5.7 Latency Budgets
The confirmed latency budgets are median < 150 ms and CPU P95
< 300 ms.
6. Failure Matrix -- Negative and Boundary Cases
The following scenarios define expected handling for invalid,
incomplete, corrupted, or unusual inputs. Where the mentor or ticket
specifies an exact HTTP status, it is stated explicitly. For other
extraction failures, the exact response status and response-body
contract must follow the agreed API error design and must not be
invented in this specification.
  ID                Failure Scenario  Input / Condition Expected Behaviour
  FM-01             Malformed Base64  Input contains    Reject the runtime
invalid Base64    request with HTTP 422.
characters or
invalid encoding. 

  FM-02             Corrupted Base64  Base64 decoding   Reject safely with HTTP
Image             succeeds, but     422.
decoded image
data is corrupted
or truncated.     

  FM-03             Non-Image Payload Valid Base64      Reject with HTTP 422.
contains text or
arbitrary binary
data instead of a
supported image.  

  FM-04             Empty Document ID document_id is  Reject with HTTP 400.
an empty string.  

  FM-05             Whitespace-Only   document_id     Reject with HTTP 400.
Document ID       contains only
whitespace.       

  FM-06             Whitespace-Only   Image payload     Reject with HTTP 400.
Payload           contains only
whitespace.       

  FM-07             Missing Vendor    Invoice does not  Report a structured
Name              contain a         mandatory-field
detectable vendor extraction or validation
name.             failure; do not
fabricate a value.

  FM-08             Missing Invoice   Invoice does not  Report a structured
Number            contain a         mandatory-field
detectable        extraction or validation
invoice number.   failure; do not
fabricate a value.

  FM-09             Missing Net       Invoice does not  Report a structured
Amount            contain a         mandatory-field
detectable net    extraction or validation
amount.           failure; do not
fabricate a value.

  FM-10             Missing Currency  Invoice does not  Report a structured
contain a         mandatory-field
detectable        extraction or validation
currency.         failure; do not
fabricate a value.

  FM-11             Zero Net Amount   Extracted         Pydantic validation must
net_amount      reject the value.
equals 0.0.     

  FM-12             Negative Net      Extracted         Pydantic validation must
Amount            net_amount is   reject the value.
less than 0.0.  

  FM-13             Invalid Currency  Extracted         Reject the invalid
currency is not a currency during entity
valid ISO-4217    validation.
currency code.    

  FM-14             Corrupt EXIF      Image contains    Handle safely without an
Metadata          malformed or      unhandled server error.
corrupted EXIF
metadata.         

  FM-15             Extreme Aspect    Image has an      Handle preprocessing
Ratio             unusually wide or safely without
tall aspect       uncontrolled processing
ratio.            or memory failure.

  FM-16             Non-UTF8 OCR      OCR adapter       Handle the decoding
Output            returns text that failure safely through a
cannot be decoded structured error path.
as valid UTF-8.   

  FM-17             Oversized Image   Image exceeds the Reject or safely handle
configured        the input without
maximum input     excessive memory
size.             consumption. The numeric
maximum size must be
defined in
implementation/runbook
configuration, not
assumed here.

  FM-18             Multi-Page Buffer Multi-page        Prevent out-of-bounds
Overrun           processing        access and handle the
attempts to       failure safely.
access data
outside the
available buffer. 

  FM-19             Rotated Document  Document image is Process safely; evaluate
rotated or        and document any
incorrectly       extraction-quality
oriented.         impact.

  FM-20             Missing Optional  An optional       Return null with low
Field             entity is absent  confidence instead of
from the          failing the complete
document.         extraction.

  FM-21             Missing Model     Required model    Fail fast; startup must
Weights           weights are       fail explicitly. Do not
absent during     use a fake fallback.
application
startup.          
FM-22             Corrupted Model   Model weights     Fail fast; startup must
Weights           cannot be loaded  fail explicitly. Do not
during            use a fake fallback.
application
startup.
6.1 Failure Handling Principles
1. Malformed Base64, corrupted image payloads, and non-image payloads
   must return HTTP 422.
2. Empty document IDs and whitespace-only image payloads must return
   HTTP 400.
3. Missing or corrupted model weights must cause an explicit startup
   failure.
4. Invalid financial values must not pass Pydantic validation.
5. Missing mandatory invoice fields must be reported as extraction or
   validation failures; values must not be fabricated.
6. Missing optional fields must not abort the entire extraction
   pipeline; represent them as null with low confidence.
7. Image-processing and OCR failures must not produce unhandled server
   errors.
8. Large or corrupted inputs must be handled safely to avoid
   uncontrolled memory consumption.
9. CI tests must be able to mock OCR without requiring external
   OS-level OCR binaries.
7. Day 14: Tuning and Performance Profiling Deliverables
The performance and tuning work must include:
- At least six documented tuning runs.
- Resolution configurations including 512x512 and 1024x1024.
- Confidence-threshold configurations including 0.50, 0.70, and
  0.85.
- OCR denoising-kernel experiments.
- A report at
  api/modules/doc_extractor/reports/tuning_experiments.md.
- Profiling using cProfile.
- A load test covering 20 concurrent extractions.
- Median and CPU P95 latency measurements.
- Memory-allocation investigation using tracemalloc, including
  checks after garbage collection for retained image-buffer
  allocations.
Only measured results may be reported. Each experiment must record its
configuration and observed outcome; do not invent or pre-fill
performance results.
8. Day 15: Diagnostics and Operational Documentation
The following deliverables are required:
- api/modules/doc_extractor/reports/diagnostic_error_analysis.md,
  including a confusion matrix, degraded-scan error rate, and
  blurry-document mitigation analysis.
- api/modules/doc_extractor/RUNBOOK.md, covering deployment,
  configured maximum file size, Prometheus metric gauges, and alert
  thresholds.
- EDPR to the staging branch using the repository's
  .github/PULL_REQUEST_TEMPLATE.md.
- Evidence for the review, including the full pytest terminal logs,
  latency percentiles, and cProfile graphs.
- A 60--90 second Loom walkthrough.
- Completion of the two-minute code-defense checklist and scheduling
  of the code defense with the Lead/CPO.
9. Acceptance Criteria
CTX-002 will be considered complete when:
1. The mocked extraction implementation has been replaced by actual
   document image processing, layout classification, and entity
   extraction.
2. MobileNetV3-Small classifies exactly the four confirmed document
   categories.
3. Classification Macro F1 is >= 0.90 on the held-out test split.
4. Bounding-box IoU is >= 0.75 for Header, Line-Item Table, and
   Totals Block.
5. Invoice entity extraction validates the required fields and
   financial constraints.
6. Invalid runtime image payloads return the required HTTP errors.
7. Missing or corrupted model weights cause explicit startup failure,
   with no fake fallback.
8. More than 60% of the module's tests cover negative and boundary
   cases, with at least 12 tests in total.
9. The full existing pytest suite passes.
10. Median CPU extraction latency is < 150 ms and CPU P95 is
    < 300 ms, supported by reproducible measurements.
11. Required tuning, diagnostic, runbook, and review evidence is
    prepared.
12. The required code defense is completed successfully.
