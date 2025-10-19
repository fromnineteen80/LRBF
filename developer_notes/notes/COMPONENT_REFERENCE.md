# ðŸš€ Material Web Components - Quick Reference

## Common Patterns & Copy-Paste Examples

### Buttons

```html
<!-- Primary action -->
<md-filled-button>Save Changes</md-filled-button>

<!-- Secondary action -->
<md-outlined-button>Cancel</md-outlined-button>

<!-- Tertiary action -->
<md-text-button>Learn More</md-text-button>

<!-- With icon -->
<md-filled-button>
    <span slot="icon" class="material-symbols-outlined">save</span>
    Save
</md-filled-button>

<!-- Icon only -->
<md-icon-button aria-label="Delete">
    <span class="material-symbols-outlined">delete</span>
</md-icon-button>

<!-- Disabled -->
<md-filled-button disabled>Submit</md-filled-button>
```

### Text Fields

```html
<!-- Basic text input -->
<md-filled-text-field 
    label="Username" 
    type="text"
    required>
</md-filled-text-field>

<!-- With icon -->
<md-filled-text-field label="Email" type="email">
    <span slot="leading-icon" class="material-symbols-outlined">email</span>
</md-filled-text-field>

<!-- Outlined variant -->
<md-outlined-text-field 
    label="Search"
    type="search">
    <span slot="leading-icon" class="material-symbols-outlined">search</span>
</md-outlined-text-field>

<!-- Password -->
<md-filled-text-field 
    label="Password" 
    type="password"
    required>
    <span slot="leading-icon" class="material-symbols-outlined">lock</span>
</md-filled-text-field>

<!-- With helper text -->
<md-filled-text-field 
    label="Username"
    supporting-text="Choose a unique username">
</md-filled-text-field>

<!-- With error -->
<md-filled-text-field 
    label="Email"
    error
    error-text="Invalid email address">
</md-filled-text-field>
```

### Cards

```html
<!-- Filled card -->
<md-filled-card>
    <h3>Daily Performance</h3>
    <p>ROI: +3.2%</p>
    <md-filled-button>View Details</md-filled-button>
</md-filled-card>

<!-- Elevated card (with shadow) -->
<md-elevated-card>
    <h3>Account Balance</h3>
    <p class="amount">$30,000</p>
</md-elevated-card>

<!-- Outlined card -->
<md-outlined-card>
    <h3>System Status</h3>
    <p>All systems operational</p>
</md-outlined-card>
```

### Checkboxes & Switches

```html
<!-- Checkbox -->
<label>
    <md-checkbox></md-checkbox>
    <span>Remember me</span>
</label>

<!-- Checkbox with value -->
<md-checkbox 
    name="terms" 
    value="accepted"
    required>
</md-checkbox>

<!-- Switch -->
<label>
    <md-switch></md-switch>
    <span>Enable notifications</span>
</label>

<!-- Radio buttons -->
<md-radio name="option" value="1"></md-radio>
<md-radio name="option" value="2"></md-radio>
```

### Selects (Dropdowns)

```html
<!-- Basic select -->
<md-select label="Choose an option">
    <md-select-option value="1">Option 1</md-select-option>
    <md-select-option value="2">Option 2</md-select-option>
    <md-select-option value="3">Option 3</md-select-option>
</md-select>

<!-- With default selection -->
<md-select label="Time period" value="30">
    <md-select-option value="7">Last 7 days</md-select-option>
    <md-select-option value="30">Last 30 days</md-select-option>
    <md-select-option value="90">Last 90 days</md-select-option>
</md-select>

<!-- Required -->
<md-select label="Account type" required>
    <md-select-option value="demo">Demo</md-select-option>
    <md-select-option value="live">Live Trading</md-select-option>
</md-select>
```

### Menus

```html
<!-- Menu with trigger button -->
<md-icon-button id="menuButton" aria-label="More options">
    <span class="material-symbols-outlined">more_vert</span>
</md-icon-button>

<md-menu 
    id="menu" 
    anchor="menuButton"
    positioning="popover">
    <md-menu-item>
        <span slot="headline">Edit</span>
    </md-menu-item>
    <md-menu-item>
        <span slot="headline">Delete</span>
    </md-menu-item>
    <md-divider></md-divider>
    <md-menu-item>
        <span slot="headline">Settings</span>
    </md-menu-item>
</md-menu>

<script>
    const button = document.getElementById('menuButton');
    const menu = document.getElementById('menu');
    button.addEventListener('click', () => {
        menu.open = !menu.open;
    });
</script>
```

### Dialogs

```html
<!-- Dialog trigger -->
<md-filled-button onclick="document.getElementById('myDialog').show()">
    Open Dialog
</md-filled-button>

<!-- Dialog -->
<md-dialog id="myDialog">
    <div slot="headline">Confirm Action</div>
    <form slot="content" id="myForm" method="dialog">
        <p>Are you sure you want to proceed?</p>
    </form>
    <div slot="actions">
        <md-text-button form="myForm" value="cancel">Cancel</md-text-button>
        <md-filled-button form="myForm" value="ok">Confirm</md-filled-button>
    </div>
</md-dialog>

<script>
    const dialog = document.getElementById('myDialog');
    dialog.addEventListener('close', (e) => {
        if (e.target.returnValue === 'ok') {
            // User confirmed
            console.log('Confirmed!');
        }
    });
</script>
```

### Progress Indicators

```html
<!-- Circular progress (loading spinner) -->
<md-circular-progress indeterminate></md-circular-progress>

<!-- Circular progress with value -->
<md-circular-progress value="0.75"></md-circular-progress>

<!-- Linear progress bar -->
<md-linear-progress indeterminate></md-linear-progress>

<!-- Linear progress with value -->
<md-linear-progress value="0.5"></md-linear-progress>
```

### Chips

```html
<!-- Assist chip -->
<md-assist-chip label="Help"></md-assist-chip>

<!-- Filter chip -->
<md-filter-chip label="Active" selected></md-filter-chip>

<!-- Input chip (removable) -->
<md-input-chip 
    label="Stock: AAPL"
    remove-only>
</md-input-chip>

<!-- Chip set -->
<md-chip-set>
    <md-filter-chip label="Stocks"></md-filter-chip>
    <md-filter-chip label="Forex"></md-filter-chip>
    <md-filter-chip label="Crypto"></md-filter-chip>
</md-chip-set>
```

### Lists

```html
<!-- Simple list -->
<md-list>
    <md-list-item>
        <div slot="headline">Item 1</div>
    </md-list-item>
    <md-list-item>
        <div slot="headline">Item 2</div>
    </md-list-item>
    <md-list-item>
        <div slot="headline">Item 3</div>
    </md-list-item>
</md-list>

<!-- List with icons -->
<md-list>
    <md-list-item>
        <span slot="start" class="material-symbols-outlined">home</span>
        <div slot="headline">Home</div>
    </md-list-item>
    <md-list-item>
        <span slot="start" class="material-symbols-outlined">settings</span>
        <div slot="headline">Settings</div>
    </md-list-item>
</md-list>

<!-- List with supporting text -->
<md-list>
    <md-list-item>
        <div slot="headline">Trading Account</div>
        <div slot="supporting-text">Balance: $30,000</div>
    </md-list-item>
</md-list>
```

### Dividers

```html
<!-- Simple divider -->
<md-divider></md-divider>

<!-- Inset divider -->
<md-divider inset></md-divider>

<!-- In a list -->
<md-list>
    <md-list-item>Item 1</md-list-item>
    <md-divider></md-divider>
    <md-list-item>Item 2</md-list-item>
</md-list>
```

---

## Form Example (Complete)

```html
<form method="POST" action="/submit">
    <!-- Text input -->
    <md-filled-text-field 
        name="username"
        label="Username" 
        type="text"
        required>
        <span slot="leading-icon" class="material-symbols-outlined">person</span>
    </md-filled-text-field>
    
    <!-- Email -->
    <md-filled-text-field 
        name="email"
        label="Email" 
        type="email"
        required>
        <span slot="leading-icon" class="material-symbols-outlined">email</span>
    </md-filled-text-field>
    
    <!-- Select -->
    <md-select name="account_type" label="Account Type" required>
        <md-select-option value="demo">Demo</md-select-option>
        <md-select-option value="live">Live Trading</md-select-option>
    </md-select>
    
    <!-- Checkbox -->
    <label style="display: flex; align-items: center; gap: 8px;">
        <md-checkbox name="terms" required></md-checkbox>
        <span>I agree to the terms</span>
    </label>
    
    <!-- Buttons -->
    <div style="display: flex; gap: 8px; margin-top: 16px;">
        <md-filled-button type="submit">Submit</md-filled-button>
        <md-outlined-button type="reset">Reset</md-outlined-button>
    </div>
</form>
```

---

## Card with Actions Example

```html
<md-elevated-card style="padding: 24px;">
    <!-- Header -->
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
        <span class="material-symbols-outlined" style="font-size: 32px; color: var(--md-sys-color-primary);">
            trending_up
        </span>
        <h2 style="margin: 0; font-size: 20px;">Daily Performance</h2>
    </div>
    
    <!-- Content -->
    <p style="margin: 16px 0; color: var(--md-sys-color-on-surface-variant);">
        Today's trading performance metrics and analysis.
    </p>
    
    <!-- Stats -->
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 24px 0;">
        <div>
            <p style="margin: 0; font-size: 12px; color: var(--md-sys-color-on-surface-variant);">ROI</p>
            <p style="margin: 4px 0 0 0; font-size: 24px; font-weight: 500; color: rgb(76, 175, 80);">+3.2%</p>
        </div>
        <div>
            <p style="margin: 0; font-size: 12px; color: var(--md-sys-color-on-surface-variant);">Trades</p>
            <p style="margin: 4px 0 0 0; font-size: 24px; font-weight: 500;">24</p>
        </div>
        <div>
            <p style="margin: 0; font-size: 12px; color: var(--md-sys-color-on-surface-variant);">Win Rate</p>
            <p style="margin: 4px 0 0 0; font-size: 24px; font-weight: 500;">68%</p>
        </div>
    </div>
    
    <!-- Divider -->
    <md-divider style="margin: 16px 0;"></md-divider>
    
    <!-- Actions -->
    <div style="display: flex; justify-content: flex-end; gap: 8px;">
        <md-text-button>Share</md-text-button>
        <md-filled-button>View Details</md-filled-button>
    </div>
</md-elevated-card>
```

---

## JavaScript Patterns

### Show/Hide Dialog

```javascript
// Show dialog
document.getElementById('myDialog').show();

// Hide dialog
document.getElementById('myDialog').close();

// Listen for close event
const dialog = document.getElementById('myDialog');
dialog.addEventListener('close', (e) => {
    console.log('Dialog closed with value:', e.target.returnValue);
});
```

### Toggle Menu

```javascript
const menu = document.getElementById('menu');
const button = document.getElementById('menuButton');

button.addEventListener('click', () => {
    menu.open = !menu.open;
});
```

### Get Form Values

```javascript
// Material Web components work with standard forms
const form = document.getElementById('myForm');
const formData = new FormData(form);

// Get specific value
const username = formData.get('username');

// Get all values as object
const data = Object.fromEntries(formData);
console.log(data);
```

### Update Progress

```javascript
const progress = document.querySelector('md-circular-progress');

// Set to 50%
progress.value = 0.5;

// Set to indeterminate
progress.indeterminate = true;
```

### Show Snackbar

```javascript
function showSnackbar(message) {
    const snackbar = document.getElementById('snackbar');
    const text = snackbar.querySelector('.snackbar-text');
    
    text.textContent = message;
    snackbar.classList.add('show');
    
    setTimeout(() => {
        snackbar.classList.remove('show');
    }, 5000);
}

// Usage
showSnackbar('Changes saved successfully!');
```

---

## Styling Tips

### Using CSS Custom Properties

```css
/* Your theme colors are automatically applied */
md-filled-button {
    --md-filled-button-container-color: var(--md-sys-color-primary);
}

/* Override specific component colors */
.success-button {
    --md-filled-button-container-color: rgb(76, 175, 80);
}
```

### Responsive Layout

```html
<!-- Use CSS Grid -->
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px;">
    <md-elevated-card>Card 1</md-elevated-card>
    <md-elevated-card>Card 2</md-elevated-card>
    <md-elevated-card>Card 3</md-elevated-card>
</div>
```

### Spacing

```html
<!-- Use utility classes from material-web-layout.css -->
<div class="mb-lg"> <!-- margin-bottom: 24px -->
    <md-filled-card class="p-lg"> <!-- padding: 24px -->
        Content
    </md-filled-card>
</div>
```

---

## Accessibility

### ARIA Labels

```html
<!-- Always add aria-label to icon-only buttons -->
<md-icon-button aria-label="Delete item">
    <span class="material-symbols-outlined">delete</span>
</md-icon-button>

<!-- Add aria-current to active navigation items -->
<a href="/dashboard" aria-current="page">Dashboard</a>
```

### Form Labels

```html
<!-- Material Web text fields include labels -->
<md-filled-text-field 
    label="Username"  <!-- This is accessible -->
    required
    aria-required="true">
</md-filled-text-field>
```

### Focus Management

```html
<!-- Focus visible is automatic with Material Web -->
<!-- Custom focus styles -->
<style>
    :focus-visible {
        outline: 2px solid var(--md-sys-color-primary);
        outline-offset: 2px;
    }
</style>
```

---

## Common Mistakes to Avoid

❌ **Don't**:
```html
<!-- Don't mix custom CSS classes with Material Web -->
<md-filled-button class="my-custom-button">Click</md-filled-button>
```

✅ **Do**:
```html
<!-- Use CSS custom properties instead -->
<md-filled-button style="--md-filled-button-container-color: red;">Click</md-filled-button>
```

---

❌ **Don't**:
```html
<!-- Don't forget to import components -->
<md-filled-button>Click</md-filled-button>
<!-- Button won't work without import! -->
```

✅ **Do**:
```html
<script type="module">
    import '@material/web/button/filled-button.js';
</script>
<md-filled-button>Click</md-filled-button>
```

---

❌ **Don't**:
```html
<!-- Don't use onclick in HTML -->
<md-filled-button onclick="myFunction()">Click</md-filled-button>
```

✅ **Do**:
```javascript
// Use addEventListener instead
const button = document.querySelector('md-filled-button');
button.addEventListener('click', myFunction);
```

---

## Resources

- **Official Docs**: https://material-web.dev/
- **Components**: https://material-web.dev/components/
- **GitHub**: https://github.com/material-components/material-web
- **Examples**: https://material-web.dev/demos/

---

**Pro Tip**: Keep this file open in a separate tab while migrating pages. Copy-paste examples and customize as needed!
