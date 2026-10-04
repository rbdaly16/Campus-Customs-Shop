# AI Prompts

This file records the prompts used while completing HW 4, along with what was missing after each first prompt and evidence of the work completed.

Evidence for HW 4 is the running site, database writes, and screenshots; no separate proof write-up is included beyond these prompts.

Future sections will use the following format:

## Problem [number]: [title]

### Prompt(s)

### What was missing after the first prompt

### Evidence

## Setup: Joke file

### Prompt(s)

HW 4

Let's work in the HW 4 folder today /joke-file

### What was missing after the first prompt

No follow-up prompt was needed; the request named the target folder and the joke-file skill.

### Evidence

Created [`joke.txt`](joke.txt) with a short homework-themed joke.

## Problem 1: Vibe coder prompts

### Prompt(s)

nice. /homework-prompt-log

### Follow-up prompt

for this one, the evidence will be the running site, database writes, and screenshots - we don't need an extra proof essay beyond these prompts

### What was missing after the first prompt

The first prompt started the log but didn't say what counts as evidence for HW 4, so the follow-up made it the running site, database writes, and screenshots.

### Evidence

Created this file, [`AI_prompts.md`](AI_prompts.md), using the same format as earlier homework logs.

## Problem 2: Analyze the database

### Prompt(s)

@"/Users/robertdaly/Downloads/data (2).zip"
Problem 2: Analyze the database 
(prblem 1 was Vide coder prompts)

can you unzip this for me and store it in a data folder. Once you do let's view the campus_customs.db and understand the fields of each table. 

Let's focus on cataloguem inventorym and users the most.

Let's also start the file output/harness.md. Let's be sure to write down each table and its fields with one concise line on why each field matters for the shop or the chatbot

### What was missing after the first prompt

No follow-up prompt was needed; the request specified the zip, destination folder, database, priority tables, and harness format.

### Evidence

Unzipped the database and 102 product photos into [`data/`](data/). Inspected the schema and contents of [`data/campus_customs.db`](data/campus_customs.db), and started [`output/harness.md`](output/harness.md) with every table and field.

## Problem 3: Build the Campus Customs website

### Prompt(s)

For Problem 1 you can count the message when I called the skills for the prompt log.

Now, Problem 3: Build the Campus Customs website
Let's focus on the front end for Campus Customs by scaffolding a React + Vite + TypeScript. Let's put a nav bar at the top that linkes to the main pages:

* Home
* Products
* About Us
* Log in
* Create account


Pull campus customs-style wording from yalebulldogblue.com for HOme and About Us, but write these pages in your own voice, which for today let's have it be the voice of Ted Lasso!

Further details:
For the Products page, show product images from the catalogue (you can use the image paths in the database) with basic product info (name, price, short description)

Make each product open a single-item page (large image on one side, full product text on the other  - descriptions, price, sizes/stock when you have them). Clicking a card on Products should take the shopper there

Add a chat interface in the bottom right of the site (a floating chat panel could be cool). I dones't need to talk to an agent just yet - a stub that will call your backend later is enough for now.

We'll also need a small API soon to read teh database. It's fine to start a simmple FastAPI app in backend/main.py just to serve products and images, then we will grow it!

### What was missing after the first prompt

No follow-up prompt was needed; the request specified the stack, nav pages, page content and voice, product and single-item layouts, chat stub, and backend scope.

### Evidence

- Running site: React + Vite + TypeScript app in [`frontend/`](frontend/) on port 5175, which proxies `/api` and `/images` to the FastAPI app in [`backend/main.py`](backend/main.py) on port 8001. The API opens the database read-only, so nothing is written yet.
- Products page loads all 102 catalogue items, and every image loads. The product page's size and stock match `inventory` (e.g. Baseball Left Chest Crewneck shows XS and XL as sold out).
- Screenshots: [home](output/screenshots/home.png), [products](output/screenshots/products.png), [product page](output/screenshots/product-page.png), [about](output/screenshots/about.png), [log in](output/screenshots/login.png), [create account](output/screenshots/create-account.png).

## Problem 4: Create account and login

### Prompt(s)

great work!

Problem 4: Create account and login

Let's build a normal create-account / login flow.
Create account: first name, last name, email, password (confirm password functionality as well)
Log in: email and password

New accounts should go into the users table and make sure to store passwords securely so hackers (human or AI) cannot access them! 

The seed database already has a test user you can use while building this

The email is test@campuscustoms.yale.edu and password is password

Let's confirm I can log in as that user and also that a brand new account I create also works. 

And then please update the output/harness.md with how auth works (what you store for a user and how passwords are protected)

### What was missing after the first prompt

No follow-up prompt was needed; the request specified the form fields, storage target, security requirement, test user, checks to run, and documentation update.

### Evidence

- Running site: logged in as the seed test user through the Log in page (nav showed "Hi, Test!"). Created a new account (Roy Kent) on Create account, then logged out and back in with it.
- Database writes in `users`: new row id 4 (`Roy Kent`, `roy.kent@example.com`, `first_name`/`last_name` set) with a `pbkdf2_sha256$600000$…` hash. The test user's legacy 120,000-iteration hash was upgraded to 600,000 on login. The plaintext password appears nowhere in the database file.
- Screenshots: [wrong password rejected](output/screenshots/login-wrong-password.png), [confirm-password mismatch blocks submit](output/screenshots/create-account-password-mismatch.png), [logged in as the new account](output/screenshots/logged-in-new-account.png).
- Auth write-up: [`output/harness.md` → Authentication](output/harness.md#authentication).

## Problem 5: PydanticAI agent backend

### Prompt(s)

great work!

PROBLEM 5: PydanticAI agent backend

Now let's build the shop chatbot as PydanticAi agent behind FastAPI, plugged into your front-end chat widget. Put the API app in backend/main.py - that is the file we run with Uvicorn.

Keep the agent as these four files next to it:

* backend/prompts/prompt.md - system promopt (grow this file later)
* backend/agent.py - agent entry/wiring
* backend/tools.py - tools the agent can call
* backend/models.py - Pydantic / PydanticAI structured types


In main.py, expose a chat route so a essage from the website returns a reply from the agent (and whatever else you need for products/auth). We will need the AI model API key for the agent.

alright so next let's put campus customs voice and safety basics into prompts/prompt.md. (we will expand tools and safety later)

Start or update types in models.py for chat replies/product catds as needed

In output/harness.md, please note how the front end talks to FastAPI and how the agent is loaded (Prompt file + model)

Make sure the backend runs from the backend/ folder like this:
uvicorn main:app --reload --port 8000

### What was missing after the first prompt

No follow-up prompt was needed. The request named the files, route, prompt contents, types, harness notes, and run command. The model and API key came from the project's AGENTS.md (Portkey, `gpt5.6-luna`).

### Evidence

- Running site: the backend runs with `uvicorn main:app --reload --port 8000` from `backend/`, and the chat widget is wired to `POST /api/chat`. On the Baseball Left Chest Crewneck page, asking "do you have this in XL?" got a correct "sold out in XL" answer. It listed six XL crewneck alternatives with product cards, and every stock count matched `inventory`.
- Database writes: each successful turn adds a user row and an assistant row to `chat_messages` (e.g. ids 23–24 for user 4, with `products_json` cards). A jailbreak attempt blocked by the provider's content filter got an in-voice refusal and was not saved.
- Screenshots: [stock answer](output/screenshots/chat-agent-stock-answer.png), [product cards in chat](output/screenshots/chat-agent-product-cards.png), [safety answer](output/screenshots/chat-agent-safety-answer.png).
- Agent files: [`backend/main.py`](backend/main.py), [`backend/agent.py`](backend/agent.py), [`backend/tools.py`](backend/tools.py), [`backend/models.py`](backend/models.py), [`backend/prompts/prompt.md`](backend/prompts/prompt.md); harness notes in [`output/harness.md`](output/harness.md#shop-chatbot-pydanticai-agent).

## Problem 6: Tools: product info and stock

### Prompt(s)

great job!

Problem 6: Tools: product info and stock

Let's give the agent tools that look up real info from campus_customs.db

Product description, price, how many are in stock (by size when customer asks)

The agent must use the database - it should not invent prices or quatnities. If a size is out of stock, say so clearly. 

Let's also expand prompts/prompt.md so the agent knows to call these tools for price and stock questios. Add or update return types in models.py as wel..

In output/harness.md list each tool and explain which model fields you chose for lookup results and why.

Let's do it!

### What was missing after the first prompt

No follow-up prompt was needed. The prompt did not say how "this" should resolve when the chat history mentions a different product, which testing exposed and the server-side page-context fix covers.

### Evidence

- Running site: the agent now has `get_product_info` and `check_stock`, alongside `search_products`. Five live chat questions (price, low stock, sold-out size, unsupported size, product we don't carry) each logged the tool calls behind the answer, and every price and quantity matched `campus_customs.db`. The table is in [`output/harness.md`](output/harness.md#verifying-the-agent-uses-the-database).
- Database writes: each test question and answer was saved to `chat_messages` for user 4 (ids 27–44).
- Screenshots: [price and stock answer](output/screenshots/chat-price-and-stock.png), [sold out in XS, matching the product page's sold-out box](output/screenshots/chat-stock-sold-out-size.png).
- Code: [`backend/tools.py`](backend/tools.py), [`backend/models.py`](backend/models.py), [`backend/prompts/prompt.md`](backend/prompts/prompt.md), [`backend/agent.py`](backend/agent.py).

## Problem 7: Chat search that updates the page

### Prompt(s)

Great job with the testing.

Problem 7: Chat search that updates the page

Let's add a cool feature to the site. When a customer askes about a type of item - ie: what hoodies do you have? - the agent should search the catalogue and the website should DYNAMIALLY show those matching items as product cards (image, name, price, short info)

This is an API contract: The agent returns structured product matches and then the front end renders them ont he website. It will look sooooo cool

After those dynamic cards are loaded by the feature, make sure the same single-tem page behaviour from Problem 3 still works: each product card - including the ones the chat just puton the page - should still open that detail view (large image + full info_ when clicked

Update prompts/prompt.md and output/harness.md so it's clear how search results reach the page.

Let's do itttt!

### Follow-up prompt

okay really good! ONly thing is that when I log in and go to Products, the From Your Chat section doesn't appear to change by user. 

I was logged in as Robert, asked about T shirts, then logged in as Test, and the From Your Chat is still showing Yale T-Shirts, even though Test never asked about those. So please fix that

### What was missing after the first prompt

The first prompt didn't say whose results the page section belongs to. A later follow-up found that one user's chat results stayed on the page after another user logged in, so results are now scoped to the shopper who asked. Testing also found two gaps, both fixed: the model's own count of results (it said 28 for 27 cards), and the open chat panel covering cards on the page.

### Evidence

- Running site: asking "what hoodies do you have?" on Home moved the site to Products and showed a "From your chat · Hoodies · 27 items" section. The 27 cards are exactly the database's 27 hoodies. "Show me navy crewnecks" showed 23 cards, matching SQL. Chat-placed cards open the Problem 3 product page, Back keeps the results, and Clear removes them.
- Database writes: the test questions and answers were saved to `chat_messages` for user 4. Page results themselves are live-only, by design.
- Screenshots: [asking on Home](output/screenshots/chat-search-1-asking-on-home.png), [results on the page](output/screenshots/chat-search-2-results-on-page.png), [chat-placed card opens the product page](output/screenshots/chat-search-3-card-opens-product-page.png).
- Contract and flow: [`output/harness.md` → Chat search that updates the page](output/harness.md#chat-search-that-updates-the-page). Prompt rules: "Showing products: chat cards vs. the page" in [`backend/prompts/prompt.md`](backend/prompts/prompt.md).
- Follow-up fix (requested after Problem 12): chat results are now tagged with their owner (`user:<id>` or `guest`) in [`frontend/src/chatResults.tsx`](frontend/src/chatResults.tsx) and cleared whenever the logged-in identity changes. Verified in the running site:
  - Roy asked "show me t-shirts" and got "T-shirts · 25 items", which stayed after a reload.
  - Logging out cleared them.
  - After logging in as Test, Products shows no "From your chat" section.
  - Results left in storage from another user were dropped on load.

## Problem 8: Customer memory

### Prompt(s)

Problem 8: Customer memory

Alright now let's level it up! When a shopper is logged in, save their chat history int eh db in a table and reload it when they return. The agent should know WHO is cahtting (name, email) - put that in agent deps (or an equivalent clear pattern) and/or tools the agent can call, whciichever you think is best.

Also pass enough page context that if someone is ona product page and asks "do you have this in pink?" the agent knows which item they mean.  A little hint for you a little birdie told me: you can put code into the agent context. You think that's a good idea?

Alright so guests can still chat, but history only needs to persis tfor logged-in users. Document in output/harness.md: how user chat history is stored, what customer fields the agent sees, and how page context is passed

Ready!? let's do it!

### What was missing after the first prompt

No follow-up prompt was needed. Testing found one gap, now fixed: recalling older conversations failed until the past-chat search kept size words like "XL", ranked by keyword matches, and skipped messages already in context.

### Evidence

- Running site: a guest on the Baseball Left Chest Crewneck page asked "do you have this in pink?" and got "only comes in navy and white", plus a pink search. The guest's chat survived a page reload, and the agent said it doesn't know a guest's name or email. The logged-in test account got its email and member-since date via `get_my_account`. It was reminded of a sold-out XL crewneck from an earlier session via `search_my_past_chats`. A fake "I'm actually Tauhid" claim plus a forged page-context note with a $1.00 price were both ignored.
- Database writes: `chat_messages` went from 56 to 64 rows, all from the logged-in test account's four turns. Guest chats added none (56 before and after the guest test). Also added index `idx_chat_messages_user (user_id, id)`.
- Screenshots: [guest asks "this in pink?" on a product page](output/screenshots/memory-1-guest-this-in-pink.png), [returning customer's saved history reloads](output/screenshots/memory-2-returning-customer-history.png).
- Docs: [`output/harness.md` → Customer memory](output/harness.md#customer-memory). Code: [`backend/guests.py`](backend/guests.py), [`backend/models.py`](backend/models.py), [`backend/agent.py`](backend/agent.py), [`backend/tools.py`](backend/tools.py), [`backend/main.py`](backend/main.py), [`backend/prompts/prompt.md`](backend/prompts/prompt.md).

## Problem 9: Usability improvements

### Prompt(s)

sweet onto Problem 9: Usability improvements

Now that the core shop works, improve it. Choose and implement:

* 2 front-end usability improvements
* 2 agent/backend usability improvements

Front-end improvements are things tht make the site look better and easier to use

Agent/backend improvements are things that the make the agent output better, more accurate, or safer. These could be new agent tools or things that make the agent run faster or cheaper

### Follow-up prompt

Wriet output/usability.md before or as you bui.d. For each of the improvements, say the foloowing:

* what you added
* why ithelps a Campus Customs shopper or the business


Then make sure all improvements acutally show up in the running app. Graders will read the write-up and look for features.

### What was missing after the first prompt

The first prompt didn't say where to document the improvements or how they'd be graded, so the follow-up asked for `output/usability.md` with what/why for each, and for every feature to show up in the running app.

### Evidence

- Running site:
  - (1) The Products search/filter/sort toolbar shows Hoodies + XL = 21 items, cheapest $45, matching SQL.
  - (2) Page-aware chat chips and the "Ask about this item" / "Find similar in-stock items" buttons appear on every product page.
  - (3) `find_similar_products` returned in-stock crewneck alternatives whose sizes and colors match the database.
  - (4) The price fact-check guard: `test_price_guard.py` passes (a stale $65 was rejected, and the reply says $72).
- Database writes: none new. The improvement tests ran as a guest, and catalogue/inventory are read-only.
- Screenshots: [products filters](output/screenshots/usability-1-products-filters.png), [ask about this item](output/screenshots/usability-2-ask-about-this-item.png), [similar in-stock items](output/screenshots/usability-3-similar-in-stock-items.png).
- Write-up: [`output/usability.md`](output/usability.md), including a reasoning-effort benchmark that was measured and not adopted.

## Problem 10: Style the website

### Prompt(s)

great job there!

Now let's do Problem 10: Style the website

Add creative design so the site feels like a real Campus Customs storefront - fonts, color. hierarchy, motion, product presentation, chat feel. More points for imaginiative and innovative design so go to town! My personal thoughts is that it would be cool to have a Handsome dan (the Yale bulldog) image floating around as the person's cursor. Not sure if you can do that but that would be cool. And double bonus is that it licks or smiles or something at each click. If that's not possible then have the image of Handsome Dan do a spin or something every now and then.

Write output/design.md: what you changed and why it should help the customer stick around and buy. Keep it concrete and concise.

### Follow-up prompt

oh man, pls also remove the green and red theme from AGENTS.md and please make this style more suitable to Yale, like Yale's blue and white. Feel free to add some Harvard jokesin there too if you find creative spots in it. Maybe in the chat as it is fetching an answer or something?

### What was missing after the first prompt

The first prompt didn't name a palette, so the site followed AGENTS.md's green-and-red rule. The follow-up removed that rule and asked for Yale blue and white plus Harvard jokes. AGENTS.md still requires creatures to be built in HTML/SVG, which is how Dan is drawn.

### Evidence

- Running site:
  - Handsome Dan (SVG) follows the cursor. On clicks he alternates lick and grin with a heart/paw burst, says "Woof!" every 5th click, and spins after 6 seconds idle. All of this was verified with real pointer events.
  - He switches off on touch screens and for reduced-motion users, and there's a footer on/off switch.
  - New fonts (Graduate / Fraunces / Inter), a Yale Blue (`#00356b`) and white palette (red kept only for warnings), a ticker, and a redesigned home page (hero badge, category tiles, game-day picks).
  - Harvard jokes in the chat's rotating fetching quips, Dan's "Beat Harvard!" bark, the ticker ("Proudly 0% crimson"), the 404 page, and the empty search state. The agent prompt allows light rivalry humor.
  - AGENTS.md: removed the green-and-red theme rule.
  - Product cards and the product page got the stage, price tag, swatches, and jersey-number sizes. The chat got the "Ask Dan" avatar, paw-print typing indicator, and happy lick on reply.
  - Mobile was checked with no sideways overflow.
- Database writes: none (styling only). `GET /api/auth/me` now returns `null` for guests instead of a 401.
- Screenshots: [home hero + Dan cursor](output/screenshots/design-1-home-hero-dan-cursor.png), [Dan licks on click](output/screenshots/design-2-dan-lick-on-click.png), [categories + picks](output/screenshots/design-3-home-categories-picks.png), [product page + Ask Dan chat](output/screenshots/design-4-product-page-chat.png), [Harvard quip while fetching](output/screenshots/design-5-chat-fetching-harvard-quip.png).
- Write-up: [`output/design.md`](output/design.md).

## Problem 11: Site testing (app check)

### Prompt(s)

awesome!

Problem 11: Site testing (app check)

Test the live site and document in output/app_check.html (a page we can double-click open). Include clear screenshots and short captions for:

1. chat checking the inventory level of an item (honest stock/price from the DB)
2. THe dynamic search-result cards appearing after a category question (ie: hoodies)
3. One of the usability features we added in Problem 9


Let's also make the html easy to grade: heading for each check, screenshot, one or two sentences on what the screenshot proves. 

And put the screenshot images files in output/app_check_images/ and link them from app_check.html with relative paths (for example app_check_images/inventory.png)

Ready!? Can you do all that!? Let's goooo!

### What was missing after the first prompt

No follow-up prompt was needed; the request named the three checks, the file and image locations, relative linking, and the per-check layout.

### Evidence

- Running site: all three checks were run live as a guest and pass.
  - (1) On the Grace Hopper College Crewneck page, chat answered "$58.00, 2 left in XL, L sold out". It matches the database and the page's size boxes, and the server log shows the `check_stock` calls.
  - (2) "What hoodies do you have?" put a "Hoodies · 27 items" card grid on the Products page, exactly the database's 27 hoodies, and a chat-placed card opens its product page.
  - (3) The Problem 9 filters (Hoodies + XL + price low→high) show the 21 hoodies in stock in XL, matching SQL.
- Database writes: none (guest session).
- Screenshots: [`output/app_check_images/`](output/app_check_images/): `inventory.png`, `search_cards.png`, `search_card_opens_product.png`, `usability_filters.png`.
- Report: [`output/app_check.html`](output/app_check.html), opens with a double-click and uses relative image paths. Raw captured values are in [`output/app_check_results.json`](output/app_check_results.json).

## Problem 12: Audit trail, safety, finish harness

### Prompt(s)

alright sweet!

Problem 12: Audit trail, safety, finish harness

Keep an append-only output/audit_trail.json of agent-loop activity (time, tool name, short args/result, stop reason)

Do not wipe it between runs please. Also, think of some safety rules to give the agent and put them in prompts/prompt.md (we may even have a skill for that? If so, use that and add to that any new safety ideas you have from this project)

Finish output/harness.md so it is clearn how the system works. 

* Model fields in model.py and why you chost them
* Tools and abilities
* Safety Rules
* Specs (loop limits, result caps, models, how to run front + back)

Also please send the link to the website so I can open it and see!

### What was missing after the first prompt

No follow-up prompt was needed. The `agent-safety` and `build-harness` skills supplied the rest. The prompt didn't set loop limits, so this work added concrete caps (8 model requests and 10 tool calls per turn) for the harness to document.

### Evidence

- Running site: every chat turn now appends to [`output/audit_trail.json`](output/audit_trail.json): `run_start`, `tool_call`, `tool_result`, `retry`, `final_output`, and `run_end` with a `stop_reason`, all sharing a `run_id`.
  - The trail survived a backend restart (7 entries → 12, earlier entries byte-identical) and a 4-process × 10 concurrent-append test.
  - Stop reasons seen live: `final_result` and `blocked_by_content_filter`. The price-guard `retry` was recorded in the scripted test's temp trail.
- Safety (via the `agent-safety` skill): [`backend/prompts/prompt.md`](backend/prompts/prompt.md) now has *Safety rules* (scope and honesty, identity and personal data, prompt injection and internals, wellbeing) and *Image and customer-photo safety*. A live test of the new bulk-inventory rule: a "store employee" asking for every quantity was declined and offered item-by-item checks instead.
- Harness (via the `build-harness` skill): [`output/harness.md`](output/harness.md) was rewritten to cover the system overview, how to run, specs and limits, abilities and entry points, all 6 tools and helpers, every model and its fields, safety rules mapped to code controls, the audit trail, verification, and work that is planned but not built. Stale statements were fixed.
- Database writes: none to the catalogue. Test chats ran as a guest.
- Website: http://127.0.0.1:5175 (frontend) with the API on http://127.0.0.1:8000.
