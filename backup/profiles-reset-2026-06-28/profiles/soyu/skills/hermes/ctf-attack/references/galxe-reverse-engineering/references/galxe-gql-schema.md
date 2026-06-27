# Galxe GraphQL Schema (Introspected Jun 2026)

## Key Mutations (197 total)

| Mutation | Returns | Required Args |
|----------|---------|---------------|
| `nonce` | String | none |
| `signin` | String (JWT) | `input: Auth {address, addressType, message, signature}` |
| `prepareParticipate` | PrepareParticipateCampaignResp | `input: PrepareParticipateInput {campaignID, address, addressType, signature, mintCount, captcha}` |
| `participate` | ParticipateCampaignResp | `input: ParticipateInput {campaignID, address, signature, nonce, chain}` |
| `verifyUserTask` | VerifyUserTaskResponse | `request: VerifyUserTaskRequest {taskId, captcha}` |
| `claimedUserTask` | ClaimedUserTaskResponse | `request: ClaimedUserTaskRequest {taskId, timestamp, captcha}` |
| `renewToken` | String | `oldToken: String!` |
| `claimCustomReward` | — | varies |

## Key Queries (199 total)

| Query | Args | Returns |
|-------|------|---------|
| `campaigns` | `input: ListCampaignInput!` | CampaignConnection |
| `campaign` | `id: ID!` | Campaign |
| `credential` | `id: ID!, eligibleAddress: String` | Credential |
| `addressInfo` | `address: String!` | UserAddressInfo |
| `getSocialAuthUrl` | `schema, type, captchaInput` | String |

## Input Types

### ListCampaignInput
`ids, listType (Enum), statuses (List), chains, types, first, after, status, claimableByUser, spaceId, rewardTypes, orderByPv, orderByUv, orderByParticipation, ...`

### ListType Enum
`Newest, Earliest, Trending, Tutorial, MostGG`

### CampaignStatus Enum
`Draft, Active, NotStarted, Expired, CapReached, Deleted`

### AddressType Enum
`COMPATIBLE, EVM, EVM_SECONDARY, SOLANA, APTOS, EMAIL, DISCORD, TWITTER, GOOGLE, TELEGRAM, WORLDCOIN, SUI, BITCOIN, TON, ...`

### Chain Enum (100+ chains)
`ETHEREUM, BSC, MATIC, ARBITRUM, OPTIMISM, BASE, LINEA, SCROLL, BLAST, ZKSYNC_ERA, GRAVITY_ALPHA, SOLANA, SUI, TON, ...`

### CaptchaInput
`lotNumber: String, captchaOutput: String, passToken: String, genTime: String, encryptedData: String`

### PrepareParticipateInput
`signature: String!, campaignID: ID!, address: String!, addressType: AddressType, mintCount: Int, chain: Chain, captcha: CaptchaInput, referralCode: String, ...`

### PrepareParticipateCampaignResp
`allow: Boolean, disallowReason: String, signature: String, nonce: String, spaceStationInfo: SpaceStation, mintFuncInfo: FuncInfo, ...`

### ParticipateCampaignResp
`participated: Boolean, failReason: String`

## Valid Campaign Fields (list query)
`id, name, status, description, rewardName, rewardType, chain, startTime, endTime, cap, numNFTMinted, thumbnail, tags, space { name }`

## INVALID Campaign Fields (causes GRAPHQL_VALIDATION_FAILED)
`numParticipants, participants { total }, credentialGroups { credentials { claimAmount, isClaimable } }`
