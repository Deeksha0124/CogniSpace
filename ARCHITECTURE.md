# CogniSpace Architecture Notes

## Brand and product direction

- App name: `CogniSpace`
- Positioning: a gentle AI wellness journal that combines reflective writing, mood tracking, sleep awareness, and supportive rewards
- UX direction: warm neutrals, low-contrast surfaces, soft rounded panels, simple English copy

## Technical approach by feature

### 1. Authentication and profile management

- Stack: Flask sessions + Werkzeug password hashing + SQLite
- Data model: `users` table with `email`, `phone`, `password_hash`, `is_new`, and `created_at`
- Isolation: every user-owned record stores `user_id`, and all reads filter by the authenticated session user
- Security: passwords are hashed with `generate_password_hash`; protected routes require login

### 2. AI journaling and multilingual input

- Stack: Hugging Face Transformers zero-shot classification pipeline
- Model choice: `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`
- Why: multilingual NLI support makes it practical to classify text from multiple input languages into English labels
- Input handling: text input plus browser voice transcription using the Web Speech API
- Output policy: recommendations and analytics remain English-only

### 3. Mood tracker

- Data model: `mood_entries`
- Structure: one entry per user, day, and time slot with color, label, score, and optional note
- Analysis: weekly aggregation by weekday and time-of-day using average mood scores
- UX: color grid for weekly patterns plus plain-language insights

### 4. Sleep tracker

- Data model: `sleep_logs`
- Structure: bedtime, wake time, computed duration, quality rating, note
- Analysis: average duration, average quality, and consistency range across recent nights
- Education: rotating sleep fact shown on login/dashboard and sleep page

### 5. Rewards and coupons

- Data model: `habit_logs`, `reward_ledger`, `coupons`
- Implementation: habits add points to the ledger; reward redemptions subtract points and create user-owned coupon records
- Decision note: a universal coupon system across arbitrary e-commerce sites is not technically dependable
- Recommendation: partner-specific integrations or an in-app marketplace are the viable architecture

## Coupon feasibility findings

- Shopify supports discount code creation for a merchant’s own store through its Admin APIs, not arbitrary third-party stores:
  [Shopify DiscountCode API](https://shopify.dev/docs/api/admin-rest/latest/resources/discountcode)
- WooCommerce similarly exposes a coupon API for a specific store installation:
  [WooCommerce Coupons API](https://woocommerce.github.io/woocommerce-rest-api-docs/)
- Conclusion: points can be converted into redeemable coupons only when LumaNest has a partnership or store-specific integration. The prototype therefore uses a partner marketplace model instead of promising universal checkout redemption.

## Voice input considerations

- Browser implementation: Web Speech API
- Limitation: browser support varies, and some browsers use server-side speech recognition:
  [MDN Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)
  [MDN SpeechRecognition](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition)

## Scaling notes

- SQLite is acceptable for a course prototype and single-machine demo
- For multi-user production scale, migrate to PostgreSQL and move auth/session storage behind a production server
- The AI inference layer should be separated into a service or queue if concurrent traffic grows
