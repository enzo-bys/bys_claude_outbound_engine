How to Connect Lemlist to an LLM Using MCP

![lemlist](https://web-assets.lemlist.com/lemlist/authors/6553321be8c20d4b3f422284_product_picto.png)

lemlist

\|

March 11, 2026

\|

5 min read

This guide walks you through connecting lemlist to your AI assistant via MCP. Once set up, you can create campaigns, pull stats, import leads, and audit sequences without ever leaving your AI client. It takes about 2 minutes.

There are 2 authentication methods

lemlist’s MCP server supports two ways to authenticate.

**OAuth (recommended)** OAuth is the simpler path. Your AI client handles the entire authentication process automatically: it opens a browser window, you log in and grant access to your lemlist team, and that’s it. No key management, no copy-pasting credentials. Access tokens are valid for 1 hour and refresh automatically for up to 30 days.

**API key** If your client doesn’t support OAuth flows, or you prefer to manage credentials manually, you can authenticate with a lemlist API key. The key is generated once inside lemlist and pasted into your client’s config file. Best for Cursor, CI environments, or custom integrations.

⚠ **Important note: the MCP server uses the X-API-Key header for authentication, which is different from the REST API's Basic Auth method.**

Setup with OAuth

Claude Desktop

Open the sidebar, click the **+** icon next to Connectors, then choose “Add custom connector”.

![](https://web-assets.lemlist.com/lemlist/CleanShot%202026-03-05%20at%2016.50.50.png)

Fill in:

- **Name:** lemlist

- **URL:**`https://app.lemlist.com/mcp`


Click “Add”. The first time you use a lemlist tool, a browser tab will open asking you to select your team and grant access.

After that, Claude handles token management in the background.

You can also add the config manually. Open `claude_desktop_config.json` and add:

1

2

3

4

5

6

7

8

```json
{
  "mcpServers": {
    "lemlist": {
      "command": "npx",
      "args": ["mcp-remote", "https://app.lemlist.com/mcp"]
    }
  }
}
```

The `mcp-remote` package manages the full OAuth flow: client discovery, browser-based consent, PKCE token exchange, and automatic refresh.

Claude Code

Run this single command in your terminal:

1

```json
claude mcp add --transport http lemlist https://app.lemlist.com/mcp
```

No `--header` flag needed. On first use, your browser will open a consent page. Once you authorize, you’re connected.

![Quote Icon](https://www.lemlist.com/quote-icon.svg)

💡 You can set up a custom lemlist agent command in Claude Code. Save the agent prompt into `.claude/commands/lemlist-agent.md`, then call it with `/lemlist-agent` to get a pre-configured assistant for campaign management.

Setup with an API key

Step 1 — Generate your lemlist API key

1. Log into lemlist and go to [app.lemlist.com](https://app.lemlist.com/)

2. Navigate to **Settings > Team > Integrations**

3. Click **“Generate”** to create a new API key

4. Copy the key and store it somewhere safe. You won’t be able to see it again after closing the page.


Step 2 — Add your key to your client

**Cursor**

1

2

3

4

5

6

7

8

9

10

```json
{
  "mcpServers": {
    "lemlist": {
      "url": "https://app.lemlist.com/mcp",
      "headers": {
        "X-API-Key": "YOUR_API_KEY"
      }
    }
  }
}
```

**Claude Desktop (npm)**

Go toSettings/Developer/Edit Config in your app.

Add a “lemlist” block to file `claude_desktop_config.json`, like in this example:

For Mac users

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

16

```json
{

  "mcpServers": {
  "lemlist": {
  "command": "npx",
  "args": [\
  "mcp-remote",\
  "https://app.lemlist.com/mcp",\
  "--header",\
  "X-API-Key: ${API_KEY}"\
  ],
    "env": {"API_KEY": "... YOUR API KEY ..."
 }
   }
     }
}
```

For Windows users

1

2

3

4

5

6

7

8

9

10

11

12

13

14

```json
{
  "lemlist": {
    "command": "C:\\PROGRA~1\\nodejs\\npx.cmd",
    "args": [\
      "mcp-remote",\
      "https://app.lemlist.com/mcp",\
      "--header",\
      "X-API-Key: ${API_KEY}"\
    ],
    "env": {
      "API_KEY": "... YOUR API KEY ..."
    }
  }
}
```

Restart Claude, and go to the Developer section

![](https://web-assets.lemlist.com/lemlist/image%20(1).png)

**Claude Code**

1

```json
claude mcp add --transport http lemlist https://app.lemlist.com/mcp --header "X-API-Key:YOUR_API_KEY"
```

Be careful: always keep your API key out of version control. If you’re working in a shared repo, use environment variables rather than hardcoding the key in your config file.

What you can do once connected

Ask your AI assistant directly: “What lemlist operations can you perform?” — it will return the most current list. The available tools evolve daily.

Typical operations include:

- **Campaign management** — create, edit, pause, or delete campaigns from chat

- **Campaign stats** — pull open rates, reply rates, and conversion funnels for any time window

- **Lead sourcing** — search lemleads by ICP criteria (role, industry, company size, location)

- **Sequence writing** — draft multi-step email sequences with variables and follow-up timing

- **Lead import** — add leads to campaigns with deduplication and enrichment options

- **Campaign audit** — identify bottlenecks in your funnel and get actionable recommendations


The lemlist agent for Claude Code

Once the MCP is connected, you can go further and set up a dedicated lemlist agent command inside Claude Code. This gives you a pre-configured expert assistant that knows how to audit campaigns, source leads, and write sequences without you having to re-explain context every time.

How to set it up

Create a file at `.claude/commands/lemlist-agent.md` inside your project folder. Paste the following prompt into it:

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

16

17

18

19

20

21

22

23

24

25

26

27

28

29

30

31

32

33

34

35

36

37

38

39

40

41

42

43

44

45

46

47

48

49

50

51

52

53

54

55

56

57

58

59

60

61

62

63

64

65

66

67

68

69

70

71

72

73

74

75

76

```json
# Lemlist Expert Agent

You are now an expert Lemlist automation specialist. Your role is to help users
maximize their cold outreach campaigns using the lemlist platform through the MCP
lemlist tools available to you.

## Your Core Identity

You are a seasoned growth hacker specializing in:

- B2B cold email outreach strategies
- Lemlist campaign optimization
- Lead generation and qualification
- Email copywriting and A/B testing
- Sales automation workflows

## Your Approach

When a user asks for help, follow this systematic methodology:

### 1. Discovery Phase

- Start by auditing existing campaigns using `get_campaigns`
- Understand the user's business context, target audience, and goals
- Analyze current performance metrics with `get_campaign_stats`

### 2. Strategy Phase

- Identify opportunities for improvement
- Propose data-driven recommendations
- Suggest lead sources using `lemleads_search` for the user's ICP
  (Ideal Customer Profile)

### 3. Execution Phase

- Create or optimize campaigns with best practices
- Write compelling email sequences following proven copywriting frameworks
  (AIDA, PAS, BAB)
- Set up proper follow-up sequences with strategic timing

### 4. Optimization Phase

- Monitor performance metrics
- Suggest A/B testing opportunities
- Iterate based on data

## Key Best Practices

### Email Copywriting

- Personalization beyond {{firstName}} (mention company, industry, recent news)
- Keep emails under 100 words
- One clear CTA per email
- Avoid salesy language, focus on value

### Campaign Strategy

- Test sending times (Tuesday-Thursday, 8-10am or 2-4pm in recipient timezone)
- Space follow-ups (Day 3, 7, 14 pattern)
- Mix question-based and value-based emails

### Lead Quality

- Quality > Quantity: Better 50 targeted leads than 500 generic ones
- Verify emails before campaigns to protect sender reputation
- Segment by persona for tailored messaging

## Safety Protocols

- Always warn about credit costs before using: findEmail, verifyEmail,
  linkedinEnrichment, findPhone
- Always preview before updating live campaigns
- Require confirmation before modifying running campaigns
- Check campaign status before making changes

Now, ask the user: "What would you like to accomplish with lemlist today?"
```

Then open Claude Code and type `/lemlist-agent` to activate it.

![Quote Icon](https://www.lemlist.com/quote-icon.svg)

💡 Think of it as a persistent context layer. Every time you call `/lemlist-agent`, Claude starts the conversation already knowing how to work with lemlist campaigns end to end.

Common questions

1. **Do I need to pay for something extra to use the MCP server?** No. The lemlist MCP server is available to all lemlist users. You just need an active lemlist account and an AI client that supports MCP.

2. **What’s the difference between OAuth and an API key in practice?** OAuth is session-based. Tokens expire and refresh automatically, so there’s nothing to manage. An API key is permanent until you revoke it, which is more convenient for automated environments but requires careful handling to avoid credential leaks.

3. **My browser didn’t open during the OAuth flow. What should I do?** Check that `mcp-remote` is installed and your terminal has permission to open URLs. You can also run `npx mcp-remote <https://app.lemlist.com/mcp`\> manually to see the consent URL and open it yourself.

4. **Can I connect multiple lemlist teams?** Yes. During the OAuth consent step, you select which team to authorize. To connect multiple teams, set up separate MCP server entries in your config, one per team.

5. **Which AI clients are supported?** Officially documented clients are Claude Desktop, Claude Code, and Cursor. Any client that supports MCP over HTTP should work with the `https://app.lemlist.com/mcp` endpoint.


You can also check the official [API](https://developer.lemlist.com/api-reference/getting-started/overview) and [MCP](https://developer.lemlist.com/mcp/setup) doc here.

![lemlist](https://web-assets.lemlist.com/lemlist/authors/6553321be8c20d4b3f422284_product_picto.png)[lemlist team](https://www.lemlist.com/authors/lemlist-team)

All-in-one solution for lead generation

WEBSITE

[https://www.lemlist.com](https://www.lemlist.com/)

[![LinkedIn](https://www.lemlist.com/linkedin.svg)](https://www.linkedin.com/company/lemlist/)

Table of Contents

[There are 2 authentication methods](https://www.lemlist.com/blog/how-to-set-up-lemlist-mcp#There%20are%202%20authentication%20methods)

[Setup with OAuth](https://www.lemlist.com/blog/how-to-set-up-lemlist-mcp#Setup%20with%20OAuth)

[Claude Desktop](https://www.lemlist.com/blog/how-to-set-up-lemlist-mcp#Claude%20Desktop)

[Claude Code](https://www.lemlist.com/blog/how-to-set-up-lemlist-mcp#Claude%20Code)

[Setup with an API key](https://www.lemlist.com/blog/how-to-set-up-lemlist-mcp#Setup%20with%20an%20API%20key)

[Step 1 — Generate your lemlist API key](https://www.lemlist.com/blog/how-to-set-up-lemlist-mcp#Step%201%20%E2%80%94%20Generate%20your%20lemlist%20API%20key)

[Step 2 — Add your key to your client](https://www.lemlist.com/blog/how-to-set-up-lemlist-mcp#Step%202%20%E2%80%94%20Add%20your%20key%20to%20your%20client)

[What you can do once connected](https://www.lemlist.com/blog/how-to-set-up-lemlist-mcp#What%20you%20can%20do%20once%20connected)

[The lemlist agent for Claude Code](https://www.lemlist.com/blog/how-to-set-up-lemlist-mcp#The%20lemlist%20agent%20for%20Claude%20Code)

[How to set it up](https://www.lemlist.com/blog/how-to-set-up-lemlist-mcp#How%20to%20set%20it%20up)

[Common questions](https://www.lemlist.com/blog/how-to-set-up-lemlist-mcp#Common%20questions)

Share this article