using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Media;


// Metachars = . $ ^ { [ ( | ) * + ? \

namespace WPFpreview
{
    // Use a dictionary with fixed keys for ComboBox options
    public static class MatchOptionKeys
    {
        public static readonly Dictionary<string, string> MatchOptions = new Dictionary<string, string>
        {
            { "_Equals", "Equals" },
            { "_NotEquals", "Does not equal" },
            { "_Contains", "Contains" },
            { "_NotContains", "Does not contain" },
            { "_BeginsWith", "Begins with" },
            { "_NotBeginsWith", "Does not begin with" },
            { "_EndsWith", "Ends with" },
            { "_NotEndsWith", "Does not end with" },
            { "_Regex", "Full Regex Match (Advanced)" }
        };
    }

    public partial class SearchText : Window
    {
        private List<Button> _quantifierButtons;
        private List<Button> _singleCharButtons;
        private bool _isExpanderExpanded;
        private bool _ignoreExpanderEvent = false;
        private bool _isAndEnabled = true; // dummy init to avoid null refs

        public SearchText()
        {
            InitializeComponent();

            // cache state of expander 
            _isExpanderExpanded = ReSafeExpander.IsExpanded;

            // Populate the ComboBox with options
            MatchComboBox.ItemsSource = MatchOptionKeys.MatchOptions.Values.ToList();
            MatchComboBox.SelectedItem = MatchOptionKeys.MatchOptions["_Contains"]; // Set default selection


            // Group ReShortctut buttons for easier enabling/disabling
            _singleCharButtons = new List<Button>
            {
                BtnLetter, BtnNum, BtnChar, BtnWhitespace, BtnSet
            };
            _quantifierButtons = new List<Button>
            {
                BtnZeroOrMore, BtnOneOrMore, BtnExactlyN, BtnRangeN, BtnOptional
            };

            RegexTooltipHelper.ApplyAll(this);

        }

        // Track last activated text box -> so regex buttons can input into any pop ups
        private TextBox _activeTextBox = null;



        private void MatchComboBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (MatchComboBox.SelectedItem == null)
            {
                return; // Ignore deselection event
            }

            // Get selected combo box value
            string comboxText = MatchComboBox.SelectedItem != null
                ? MatchComboBox.SelectedItem.ToString()
                : "";
            // Reverse lookup to get the key from the value
            string matchMode = MatchOptionKeys.MatchOptions.FirstOrDefault(pair => pair.Value == comboxText).Key;

            if (matchMode == "_Regex")
            {
                // Cache user state before forcing collapsing the expander
                _isExpanderExpanded = ReSafeExpander.IsExpanded;
                _ignoreExpanderEvent = true;
                ReSafeExpander.IsExpanded = false;
                _ignoreExpanderEvent = false;
                var toggle = ReSafeExpander.Template.FindName("HeaderToggleButton", ReSafeExpander) as ToggleButton;
                toggle.IsEnabled = false;
                ReSafeExpander.Header = "Full Regex Mode";
                // Add toggle tip for full regx mode 
                var headerTextBlock = ReSafeExpander.Template.FindName("HeaderText", ReSafeExpander) as TextBlock;
                headerTextBlock.ToolTip =
                    "Full Regex Mode:\n" +
                    "• Enter a custom regular expression using standard syntax, the same as\n" +
                    "  that in SafeRegex but without the outer square brackets\n" +
                    "• Meta characters include: .  $  ^  {  [  (  |  )  *  +  ?  \\\n" +
                    "• To match these characters literally, escape them with a backslash (e.g., \\., \\$, \\[).\n" +
                    "• Use grouping (parentheses), character sets ([abc]), and quantifiers ({n}, *, +, ?).\n" +
                    "• Buttons and safe regex features are disabled in this mode.\n" +
                    "• For help, see Regex documentation online.";
                // Hide match case checkbox from UI 
                MatchCaseCheckBox.Visibility = Visibility.Collapsed;
                // Shift AnnotationTagsCheckBox to column 1
                Grid.SetColumn(AnnotationTagsCheckBox, 1);
                // Upate search logic to skip safe regex compiler
            }
            else
            {
                // Restore normal behavior of expander 
                ReSafeExpander.IsExpanded = _isExpanderExpanded;
                ReSafeExpander.ClearValue(Expander.HeaderProperty);
                var headerTextBlock = ReSafeExpander.Template.FindName("HeaderText", ReSafeExpander) as TextBlock;
                if (headerTextBlock != null)
                    headerTextBlock.ClearValue(TextBlock.ToolTipProperty);
                // Re-enable toggle
                var toggle = ReSafeExpander.Template.FindName("HeaderToggleButton", ReSafeExpander) as ToggleButton;
                if (toggle != null)
                    toggle.IsEnabled = true;
                // Shift AnnotationTagsCheckBox back to column 2
                Grid.SetColumn(AnnotationTagsCheckBox, 2);
                // Re-display match case 
                MatchCaseCheckBox.Visibility = Visibility.Visible;
                // Update BtnAndOr to include 'And' Condition if appropriate
                if (matchMode == "_Contains" || matchMode == "_NotContains")
                {
                    // Enable and or functionality 
                    BtnAndOr.Content = "Or [|] / And [§]";
                    _isAndEnabled = true;
                }
                else
                {
                    // restore default content
                    BtnAndOr.Content = "Or [|]";
                    _isAndEnabled = false;
                }

            }
        }

        // need to remove tooltip for grp mode prompts

        private void SearchButton_Click(object sender, RoutedEventArgs e)
        {
            // Get entered text
            string enteredText = InputTextBox.Text;

            // Get selected combo box value
            string comboxText = MatchComboBox.SelectedItem != null
                ? MatchComboBox.SelectedItem.ToString()
                : "";
            // Reverse lookup to get the key from the value
            string matchMode = MatchOptionKeys.MatchOptions.FirstOrDefault(pair => pair.Value == comboxText).Key;

            // Get Match Case checkbox states
            bool isMatchCase = MatchCaseCheckBox.IsChecked == true;

            // Compile the safe regex from input text, Match mode, and Match Case
            string regexText = SafeRegex.SafeRe_Compiler(enteredText, matchMode, isMatchCase);

            // Get Include Annotation tags checkbox state
            bool isAnnotationTags = AnnotationTagsCheckBox.IsChecked == true;

            // Example: Show all values in a message box
            MessageBox.Show(
                $"Text: {enteredText}\n" +
                $"Compiled Regex: {regexText}\n" +
                $"Match: {matchMode}\n" +
                $"Match Case: {isMatchCase}\n" +
                $"Include Annotation tags: {isAnnotationTags}",
                "Search Info"
            );
        }

        private bool _GroupMode = false;
        private bool _HasSelection = false;

        // Mini helper function for inserting a string into a TextBox at caret or selection
        private void InsertTagAtCaret(TextBox targetTextBox, string tag, string placeholder = null)
        {
            if (targetTextBox == null || string.IsNullOrEmpty(tag)) return;

            // Get current caret position
            int caretIndex = targetTextBox.CaretIndex;

            // Insert the tag at caret
            targetTextBox.Text = targetTextBox.Text.Insert(caretIndex, tag);

            if (!string.IsNullOrEmpty(placeholder))
            {
                // Find the placeholder within the inserted tag
                int placeholderStart = caretIndex + tag.IndexOf(placeholder, StringComparison.Ordinal);
                int placeholderLength = placeholder.Length;

                // Select the placeholder text
                targetTextBox.SelectionStart = placeholderStart;
                targetTextBox.SelectionLength = placeholderLength;
            }
            else
            {
                // No placeholder → just move caret to end of inserted text
                targetTextBox.CaretIndex = caretIndex + tag.Length;
            }

            targetTextBox.Focus();
        }

        // Handle special buttons with custom logic so can select placeholder
        private void HandleSpecialInsert(Button button, TextBox targetTextBox)
        {
            if (button == null || targetTextBox == null) return;

            if (!(button.Tag is string tagString) || string.IsNullOrEmpty(tagString))
                return;

            string placeholder = null;

            // If the tag is wrapped in square brackets or double brackets, strip outer brackets
            if (tagString.StartsWith("[[") && tagString.EndsWith("]]") && tagString != BtnLetter.Tag.ToString()) // [[abc]]
            {
                placeholder = tagString.Substring(2, tagString.Length - 4);
            }
            else if (tagString.StartsWith("[{") && tagString.EndsWith("}]")) // [{N}], [{N,M}]
            {
                placeholder = tagString.Substring(2, tagString.Length - 4);
            }

            if (placeholder != null)
            {
                // Insert tag and select placeholder text for easy replacement
                InsertTagAtCaret(targetTextBox, tagString, placeholder);
            }
            else
            {
                // Otherwise, just insert the tag as-is
                InsertTagAtCaret(targetTextBox, tagString);
            }
        }



        private void ReShortcutButton_Click(object sender, RoutedEventArgs e)
        {
            var button = sender as Button;
            if (button == null) return;

            // Group mode handling
            if (_GroupMode)
            {
                if (button == BtnAndOr) // Cancel
                {
                    bool Cancelled = true;
                    ExitGroupMode(Cancelled);
                }
                else if (button == BtnGroup && _HasSelection) // Apply
                {
                    ApplyGroup();
                }
                else if (_quantifierButtons.Contains(button)) // Quantifier button in group mode
                {
                    // Use helper to append quantifier at the end of the current group selection
                    var targetTextBox = _activeTextBox ?? InputTextBox;
                    HandleSpecialInsert(button, targetTextBox);
                    ExitGroupMode();
                }

                // Prevent default behavior for all other buttons
                return;
            }

            // Normal mode
            if (button.Tag is string tagString)
            {
                if (button.Name == "BtnAndOr")
                {
                    OrPopup.IsOpen = true;
                    HandleOrPopupOpened();
                }
                else if (button.Name == "BtnGroup")
                {
                    HandleGroupSelection(sender, e);
                }
                else
                {
                    var targetTextBox = _activeTextBox ?? InputTextBox;
                    HandleSpecialInsert(button, targetTextBox);
                }
            }
        }

        private void InputTextBox_TextChanged(object sender, TextChangedEventArgs e)
        {
            UpdateHintVisibility();
        }

        private void InputTextBox_GotFocus(object sender, RoutedEventArgs e)
        {
            _activeTextBox = InputTextBox;
            UpdateHintVisibility();
        }

        private void InputTextBox_LostFocus(object sender, RoutedEventArgs e)
        {
            UpdateHintVisibility();
        }

        private void UpdateHintVisibility()
        {
            InputHint.Visibility = string.IsNullOrEmpty(InputTextBox.Text) && !InputTextBox.IsFocused
                ? Visibility.Visible
                : Visibility.Collapsed;
        }

        private void ReSafeExpander_Expanded(object sender, RoutedEventArgs e)
        {
            if (_ignoreExpanderEvent) return;
            _isExpanderExpanded = true;
        }

        private void ReSafeExpander_Collapsed(object sender, RoutedEventArgs e)
        {
            if (_ignoreExpanderEvent) return;
            _isExpanderExpanded = false;
        }



        // Enable or disable groups of buttons
        private void SetButtonGroupState(IEnumerable<Button> buttons, bool enabled)
        {
            foreach (var b in buttons)
                b.IsEnabled = enabled;
        }

        private void HandleGroupSelection(object sender, RoutedEventArgs e)
        {
            _GroupMode = true;
            Cache_States();
            ApplyCancel_BtnUI();
            GrpModeBtn_StateSetter();
            // Check if user already has text selected
            if (!string.IsNullOrEmpty(InputTextBox.SelectedText))
            {  
                SelectedText_Present();
            }
        }

        private void GrpModeBtn_StateSetter()
        {
            // Disable all buttons except logic buttons  
            SetButtonGroupState(_quantifierButtons, false);
            SetButtonGroupState(_singleCharButtons, false);
            MatchComboBox.IsEnabled = false;
            MatchCaseCheckBox.IsEnabled = false;
            AnnotationTagsCheckBox.IsEnabled = false;
            SearchButton.IsEnabled = false;

            var toggle = ReSafeExpander.Template.FindName("HeaderToggleButton", ReSafeExpander) as ToggleButton;
            toggle.IsEnabled = false;


            // Highlight textbox to indicate "selection mode"
            InputTextBox.BorderBrush = Brushes.Green;
            InputTextBox.BorderThickness = new Thickness(2);
            InputTextBox.Focus();

            // Give user hints to select text in expander header 
            ReSafeExpander.Header = "Select (Shift + Arrows) text to group";
            // Ensure tooltip does not show
            var headerTextBlock = ReSafeExpander.Template.FindName("HeaderText", ReSafeExpander) as TextBlock;
            if (headerTextBlock != null)
            {
                ToolTipService.SetShowOnDisabled(headerTextBlock, false);
            }
        }

        private void ApplyCancel_BtnUI()
        {
            BtnGroup.Background = Brushes.Transparent;
            BtnGroup.BorderBrush = Brushes.Green;
            BtnGroup.Foreground = Brushes.Green;
            BtnGroup.Content = "Apply Group";
            BtnGroup.IsEnabled = false;

            BtnAndOr.Background = Brushes.Transparent;
            BtnAndOr.BorderBrush = Brushes.Red;
            BtnAndOr.Foreground = Brushes.Red;
            BtnAndOr.Content = "Cancel (Esc)";
        }

        private void InputTextBox_SelectionChanged(object sender, RoutedEventArgs e)
        {
            SelectedText_Present();
        }

        private void SelectedText_Present()
        {
            if (_GroupMode)
            {
                _HasSelection = InputTextBox.SelectionLength > 0;

                // Enable "Apply Group" when text is highlighted
                BtnGroup.IsEnabled = _HasSelection;
                BtnGroup.Foreground = _HasSelection ? Brushes.Green : Brushes.Gray;
            }
        }

        // Apply group logic
        private void ApplyGroup()
        {
            if (!_HasSelection) return;

            int selStart = InputTextBox.SelectionStart;
            int selLength = InputTextBox.SelectionLength;

            string selected = InputTextBox.Text.Substring(selStart, selLength);
            string grouped = $"[({selected})]";

            // Replace selection with grouped text
            InputTextBox.Text = InputTextBox.Text.Remove(selStart, selLength)
                                  .Insert(selStart, grouped);

            // Reset caret
            InputTextBox.CaretIndex = selStart + grouped.Length;

            // Re-enable quantifiers only
            SetButtonGroupState(_quantifierButtons, true);

            // Give user hint to add quantifier or finish
            ReSafeExpander.Header = "Add a quantifier";
        }


        private object _defaultGroupContent;
        private object _defaultAndOrContent;
        private object _cachedInputBoxText;

        // cache default button content on load so reset back to orginal after group mode 
        private void Cache_States()
        {
            _defaultGroupContent = BtnGroup.Content;
            _defaultAndOrContent = BtnAndOr.Content;
            _cachedInputBoxText = InputTextBox.Text;
        }


        // Cancel or cleanup
        private void ExitGroupMode(bool Cancelled=false)
        {
            _GroupMode = false;
            _HasSelection = false;

            // Reset UI
            BtnGroup.ClearValue(Button.BackgroundProperty);
            BtnGroup.ClearValue(Button.ForegroundProperty);
            BtnGroup.ClearValue(Button.BorderBrushProperty);
            BtnGroup.ClearValue(Button.IsEnabledProperty);
            BtnGroup.Content = _defaultGroupContent;

            BtnAndOr.ClearValue(Button.BackgroundProperty);
            BtnAndOr.ClearValue(Button.ForegroundProperty);
            BtnAndOr.ClearValue(Button.BorderBrushProperty);
            BtnAndOr.ClearValue(Button.ContentProperty);
            BtnAndOr.ClearValue(Button.IsEnabledProperty);
            BtnAndOr.Content = _defaultAndOrContent;


            InputTextBox.ClearValue(TextBox.BorderBrushProperty);
            InputTextBox.ClearValue(TextBox.BorderThicknessProperty);
            // Restore text if cancelled
            if (Cancelled)
            {
                InputTextBox.Text = _cachedInputBoxText?.ToString() ?? "";
            }

            var toggle = ReSafeExpander.Template.FindName("HeaderToggleButton", ReSafeExpander) as ToggleButton;
            toggle.IsEnabled = true;
            // Restore dynamic trigger behaviour
            ReSafeExpander.ClearValue(Expander.HeaderProperty);

            // Revert tooltip behaviour
            var headerTextBlock = ReSafeExpander.Template.FindName("HeaderText", ReSafeExpander) as TextBlock;
            if (headerTextBlock != null)
            {
                ToolTipService.SetShowOnDisabled(headerTextBlock, true);
            }

            // Re-enable everything
            SetButtonGroupState(_quantifierButtons, true);
            SetButtonGroupState(_singleCharButtons, true);
            MatchComboBox.IsEnabled = true;
            MatchCaseCheckBox.IsEnabled = true;
            AnnotationTagsCheckBox.IsEnabled = true;
            SearchButton.IsEnabled = true;
        }



        // Below is the code for handling the OR popup functionality
        private TextBox _activePopupTextBox;


        /// <summary>
        /// Called when the OR popup is opened. Handles switching AND/OR,
        /// adding textboxes, routing shortcut button clicks, collecting input, etc.
        /// </summary>
        private void HandleOrPopupOpened()
        {
            PopBtnAddBox.Click -= PopBtnAddBox_Click;
            PopBtnAddBox.Click += PopBtnAddBox_Click;

            PopBtnRmvBox.Click -= PopBtnRmvBox_Click;
            PopBtnRmvBox.Click += PopBtnRmvBox_Click;

            AndOrToggle.Click -= AndOrToggle_Click;
            AndOrToggle.Click += AndOrToggle_Click;

            PopBtnClose.Click -= PopBtnClose_Click;
            PopBtnClose.Click += PopBtnClose_Click;

            PopBtnOk.Click -= PopBtnOk_Click;
            PopBtnOk.Click += PopBtnOk_Click;
        }

        /// <summary>
        /// Switch between AND / OR
        /// </summary>
        private void AndOrToggle_Click(object sender, RoutedEventArgs e)
        {
            if (AndOrToggle.Content?.ToString() == "Mode: AND")
            {
                AndOrToggle.Content = "Mode: OR";
                foreach (var lab in ConditionPanel.Children.OfType<Label>())
                {
                    lab.Content = "OR";
                }
            }
            else
            {
                AndOrToggle.Content = "Mode: AND";
                foreach (var lab in ConditionPanel.Children.OfType<Label>())
                {
                    lab.Content = "AND";
                }
            }
        }

        /// <summary>
        /// Reset state when popup is opened
        /// </summary> 
        private void OrPopup_Opened(object sender, EventArgs e)
        {
            // Reset toggle
            AndOrToggle.Content = "Mode: OR";

            // if AND is not applicable, disable button and set to AND
            if (_isAndEnabled)
            {
                AndOrToggle.IsEnabled = true;
            }
            else
            {
                AndOrToggle.IsEnabled = false;
            }

                // Disable Buttons in form
                popUpBtnSettings(false);

            // Set Remove button state to false 
            PopBtnRmvBox.IsEnabled = false;

            // Clear old textboxes
            ConditionPanel.Children.Clear();

            // Always add 2 fresh ones
            AddConditionTextBox();
            AddAndOrLabel();
            AddConditionTextBox();

        }

        /// <summary>
        /// Add another textbox
        /// </summary>
        private void PopBtnAddBox_Click(object sender, RoutedEventArgs e)
        {
            AddAndOrLabel();
            AddConditionTextBox();
            if (ConditionPanel.Children.OfType<TextBox>().Count() > 2)
            {
                PopBtnRmvBox.IsEnabled = true;
            }
            else
            {
                PopBtnRmvBox.IsEnabled = false;
            }
        }

        private void PopBtnRmvBox_Click(object sender, RoutedEventArgs e)
        {
            if (ConditionPanel.Children.OfType<TextBox>().Count() > 2)
            {
                RmvoveConditionTextBox();
                RemoveAndOrLabel();
                if (ConditionPanel.Children.OfType<TextBox>().Count() > 2)
                {
                    PopBtnRmvBox.IsEnabled = true;
                }
                else
                {
                    PopBtnRmvBox.IsEnabled = false;
                }
            }
        }

        /// <summary>
        /// Closes the popup
        /// </summary>
        private void PopBtnClose_Click(object sender, RoutedEventArgs e)
        {
            ClosePopUp();
        }

        private void ClosePopUp()
        {
            OrPopup.IsOpen = false;
            // Re-enable dsiabled buttons 
            popUpBtnSettings(true);
            // Reset last active textbox to main window
            _activeTextBox = InputTextBox;
        }

        private void popUpBtnSettings(bool enabled)
        {
            BtnAndOr.IsEnabled = enabled;
            MatchComboBox.IsEnabled = enabled;
            SearchButton.IsEnabled = enabled;
            AnnotationTagsCheckBox.IsEnabled = enabled;
            MatchCaseCheckBox.IsEnabled = enabled;
            var toggle = ReSafeExpander.Template.FindName("HeaderToggleButton", ReSafeExpander) as ToggleButton;
            toggle.IsEnabled = enabled;

        }



        /// <summary>
        /// Collect all states and insert into main textbox
        /// </summary>
        private void PopBtnOk_Click(object sender, RoutedEventArgs e)
        {
            bool isAnd = AndOrToggle.Content?.ToString().EndsWith("AND") == true;

            // Collect non-empty textbox values
            var textParts = ConditionPanel.Children
                .OfType<TextBox>()
                .Where(tb => !string.IsNullOrWhiteSpace(tb.Text))
                .Select(tb => tb.Text.Trim())
                .ToList();

            if (!textParts.Any())
                return; // nothing to insert

            string finalPattern;

            if (isAnd)
            {
                // AND logic using positive lookaheads
                // Each textbox wrapped in (?=.*text)
                string joinPattern = string.Join("§", textParts);
                finalPattern = $"[({joinPattern})]";
            }
            else
            {
                // OR logic: wrap each in () and join with |
                string joinPattern = string.Join("[|]", textParts);
                finalPattern = $"[({joinPattern})]";
            }

            // Insert into main textbox at caret position
            int caretIndex = InputTextBox.CaretIndex;
            InputTextBox.Text = InputTextBox.Text.Insert(caretIndex, finalPattern);
            InputTextBox.CaretIndex = caretIndex + finalPattern.Length;

            // Close and reset popup
            ClosePopUp();
        }

        /// <summary>
        /// Utility to add a textbox to the popup panel
        /// </summary>
        private void AddConditionTextBox()
        {
            var tb = new TextBox
            {
                MinWidth = 120,
                MinHeight = 25,
                Margin = new Thickness(0, 5, 0, 0)
            };

            // Track last active textbox within pop up for add / remove
            tb.GotFocus += (s, e) => _activePopupTextBox = tb;
            // Track global last active text box for regex buttons 
            tb.GotFocus += (s, e) => _activeTextBox = tb;

            ConditionPanel.Children.Add(tb);

            // Set as active by default when added
            _activePopupTextBox = tb;
        }

        private void RmvoveConditionTextBox()
        {
            if (_activePopupTextBox != null && ConditionPanel.Children.Contains(_activePopupTextBox))
            {
                ConditionPanel.Children.Remove(_activePopupTextBox);
                _activePopupTextBox = null;
            }
            else
            {
                // If no active textbox, remove the last one
                ConditionPanel.Children.RemoveAt(ConditionPanel.Children.Count - 1);
            }
        }

        private void AddAndOrLabel()
        {
            // Get either AND or OR string
            var mode_AndOr = AndOrToggle.Content.ToString().Split(':')[1].Trim();

            var lab = new Label
            {
                Content = mode_AndOr,
                FontWeight = FontWeights.Bold,
                FontSize = 15, 
                Height = 25,
                HorizontalAlignment = HorizontalAlignment.Stretch,
                HorizontalContentAlignment = HorizontalAlignment.Center,
                Padding = new Thickness(0, -5, 0, 0),
                BorderBrush = Brushes.Gray,
                Margin = new Thickness(0, 5, 0, 0),
                BorderThickness = new Thickness(1),
                Background = Brushes.LightGray
            };

            ConditionPanel.Children.Add(lab);
        }

        private void RemoveAndOrLabel()
        {
            // Remove the label before it (AND/OR label)
            var lastLabel = ConditionPanel.Children.OfType<Label>().LastOrDefault();
            if (lastLabel != null)
                ConditionPanel.Children.Remove(lastLabel);
        }


    }

    /// <summary>
    /// ///////////////////////SafeRegex Btns ToolTip Helper//////////////////////////////
    /// </summary>
    /// 
    public class RegexTooltipHelper
    {
        // Simple struct-like object without properties (easier to port to Python)
        public class TooltipData
        {
            public string Overview;
            public string Examples;
        }

        // Central dictionary of regex tooltips
        private static readonly Dictionary<string, TooltipData> Tooltips =
            new Dictionary<string, TooltipData>
            {
            { "BtnLetter", new TooltipData {
                Overview = "Matches any single uppercase or lowercase letter.",
                Examples = "[a-z] → lowercase; [A-Z] → uppercase; [a-zA-Z] → any letter"
            }},
            { "BtnNum", new TooltipData {
                Overview = "Matches a single digit between 0 and 9.",
                Examples = "[\\d] → same as [0-9]"
            }},
            { "BtnChar", new TooltipData {
                Overview = "Matches any single character except a line break.",
                Examples = "[.] → matches a, Z, %, etc. (not newline)"
            }},
            { "BtnWhitespace", new TooltipData {
                Overview = "Matches any kind of whitespace character.",
                Examples = "[\\s] → spaces, tabs, line breaks"
            }},
            { "BtnZeroOrMore", new TooltipData {
                Overview = "Matches zero or more of the preceding element.",
                Examples = "a[*] → \"\", \"a\", \"aa\", \"aaa\""
            }},
            { "BtnOneOrMore", new TooltipData {
                Overview = "Matches one or more of the preceding element.",
                Examples = "a[+] → \"a\", \"aa\", \"aaa\""
            }},
            { "BtnExactlyN", new TooltipData {
                Overview = "Matches exactly N repetitions of the preceding element.",
                Examples = "a[{3}] → \"aaa\""
            }},
            { "BtnRangeN", new TooltipData {
                Overview = "Matches between N and M repetitions.",
                Examples = "a[{2,4}] → \"aa\", \"aaa\", \"aaaa\"; a[{2,}] → 2+"
            }},
            { "BtnOptional", new TooltipData {
                Overview = "Makes the preceding element optional.",
                Examples = "colou[?]r → \"color\" or \"colour\""
            }},
            { "BtnSet", new TooltipData {
                Overview = "Matches any one character from the set or range.",
                Examples = "[abc] → a, b, or c; [A-Z] → uppercase"
            }},
            { "BtnAndOr", new TooltipData {
                Overview = "Acts as a logical OR between two expressions.",
                Examples = "cat[|]dog → matches \"cat\" or \"dog\""
            }},
            { "BtnGroup", new TooltipData {
                Overview = "Groups part of the pattern as a single unit.",
                Examples = "(abc)[+] → \"abc\", \"abcabc\", ..."
            }}
            };

        // Assign tooltips to all registered buttons
        public static void ApplyAll(Window window)
        {
            foreach (var kvp in Tooltips)
            {
                var btn = window.FindName(kvp.Key) as Button;
                if (btn != null)
                {
                    btn.ToolTip = BuildTooltip(kvp.Value);
                }
            }
        }

        // Build a tooltip stackpanel for Overview + Examples
        private static ToolTip BuildTooltip(TooltipData data)
        {
            var stack = new StackPanel { MaxWidth = 300 };

            stack.Children.Add(new TextBlock
            {
                Text = "Overview:",
                FontWeight = FontWeights.Bold,
                Margin = new Thickness(0, 0, 0, 2)
            });
            stack.Children.Add(MakeFormattedText(data.Overview, true));

            stack.Children.Add(new TextBlock
            {
                Text = "Examples:",
                FontWeight = FontWeights.Bold,
                Margin = new Thickness(0, 8, 0, 2)
            });
            stack.Children.Add(MakeFormattedText(data.Examples, true));

            return new ToolTip { Content = stack };
        }

        // Bold everything in square brackets
        private static TextBlock MakeFormattedText(string input, bool wrap)
        {
            var tb = new TextBlock { TextWrapping = wrap ? TextWrapping.Wrap : TextWrapping.NoWrap };
            int start = 0;

            while (start < input.Length)
            {
                int open = input.IndexOf('[', start);
                if (open == -1)
                {
                    tb.Inlines.Add(input.Substring(start));
                    break;
                }

                if (open > start)
                    tb.Inlines.Add(input.Substring(start, open - start));

                int close = input.IndexOf(']', open);
                if (close == -1)
                {
                    tb.Inlines.Add(input.Substring(open));
                    break;
                }

                string inside = input.Substring(open, close - open + 1);
                tb.Inlines.Add(new Run(inside) { FontWeight = FontWeights.Bold });

                start = close + 1;
            }

            return tb;
        }
    }


    /// <summary>
    /// ///////////////////////SafeRE Compiler//////////////////////////////
    /// </summary>

    public static class SafeRegex
    {

        public static string SafeRe_Compiler(string input, string matchMode, bool isMatchcase)
        {
            if (matchMode == "_Regex")
            {
                // Full regex mode, return input as-is 
                return input;
            }
            // Process input text first
            string output = CompileSafeRegex(input);
            // Final pass: replace tokens with real regex character classes
            output = Regex.Replace(output, @"__SET__(.*?)__ENDSET__", "[$1]");
            // Apply match style
            output = ApplyMatchStyle(output, matchMode, isMatchcase);

            return output;

        }


        private static string CompileSafeRegex(string input)
        {
            string output = input;

            while (true)
            {
                var segments = FindBracketSegments(output);

                //////////// Show all found segments in a MessageBox for debugging
                if (segments.Count > 0)
                {
                    var sb = new StringBuilder();
                    for (int i = 0; i < segments.Count; i++)
                    {
                        sb.AppendLine($"Segment {i + 1}: {segments[i].Content} (Start: {segments[i].Start}, End: {segments[i].End})");
                    }
                    MessageBox.Show(sb.ToString(), "Segments Found");
                }
                ////////////

                if (segments.Count == 0) break;

                foreach (var seg in segments)
                {
                    string processed = ProcessSegment(seg.Content);
                    MessageBox.Show($"Processing segment: {seg.Content} -> {processed}");
                    output = output.Substring(0, seg.Start) + processed + output.Substring(seg.End + 1);
                    MessageBox.Show($"Intermediate output: {output}");
                    break; // restart after each replacement (indexes will shift)
                }
            }
            
            return output;
        }

        private static string ProcessSegment(string content)
        {

            // Rule: Curly quantifier e.g. [{3}], [{3,4}], [{3,}]
            if (content.StartsWith("{") && content.EndsWith("}"))
            {
                string inner = content.Substring(1, content.Length - 2);
                // Validate contents: only digits and at most one comma
                if (Regex.IsMatch(inner, @"^\d+(,\d*)?$"))
                {
                    return "{" + inner + "}";
                }
                // Invalid contents -> escape segment
                MessageBox.Show($"Invalid quantifier content: {inner}, escaping entire segment: {Regex.Escape(content)} where content = {content}");
                return Regex.Escape(content);
            }

            // Rule: Double square brackets e.g. [[abc]] -> [abc]
            if (content.StartsWith("[") && content.EndsWith("]"))
            {
                // Add custom tag so we dont reprocess [abc] in FindBracketSegments in next loop
                string inner = content.Substring(1, content.Length - 2);
                string innerEscaped = Regex.Escape(inner);
                return $"__SET__{innerEscaped}__ENDSET__";
            }

            // Rule: Parentheses e.g. [(...)]
            if (content.StartsWith("(") && content.EndsWith(")"))
            {
                string inner = content.Substring(1, content.Length - 2);

                // Custom AND logic 
                if (inner.Contains("§"))  
                {
                    var terms = inner.Split('§');
                    var lookaheads = terms.Select(term => $"(?=.*({CompileSafeRegex(term)}))");
                    return string.Concat(lookaheads);
                }
                else
                {
                    string cleaned = CompileSafeRegex(inner);
                    return "(" + cleaned + ")";
                }
            }

            // Rule: Single-token wrappers e.g. [\d], [.], [^]
            if (IsAllowedToken(content))
            {
                return content;
            }

            MessageBox.Show($"Content '{content}' is invalid, escaping entire segment.");

            // Default: escape whole block
            return Regex.Escape(content);
        }

        private static bool IsAllowedToken(string content)
        {
            // Allowed escape tokens like \d, \w, \s etc
            if (Regex.IsMatch(content, @"^\\[dws]$")) return true;

            // Allowed literal meta-chars: . + * ? ^ $ |
            if (" .+*?^$|".Contains(content)) return true;

            return false;
        }

        private class BracketSegment
        {
            public int Start { get; }
            public int End { get; }
            public string Content { get; }

            public BracketSegment(int start, int end, string content)
            {
                Start = start;
                End = end;
                Content = content;
            }
        }

        private static List<BracketSegment> FindBracketSegments(string input)
        {
            var stack = new Stack<int>();
            var segments = new List<BracketSegment>();

            // Handle double square brackets [[...]] as would naturally produce two segments when we only want [abc]
            for (int i = 0; i < input.Length; i++)
            {
                // Detect double [[
                if (i + 1 < input.Length && input[i] == '[' && input[i + 1] == '[')
                {
                    stack.Push(i);      // push the first [
                    i++;                // skip the second [
                    continue;
                }

                // Detect double ]]
                if (i + 1 < input.Length && input[i] == ']' && input[i + 1] == ']')
                {
                    if (stack.Count > 0)
                    {
                        int start = stack.Pop();
                        int end = i + 1; // include both ]]
                        string content = input.Substring(start + 2, end - start - 3); // remove outer [[ ]]
                        segments.Add(new BracketSegment(start, end, "[" + content + "]"));
                    }
                    i++; // skip the second ]
                    continue;
                }

                // Normal single [] handling
                if (input[i] == '[')
                {
                    stack.Push(i);
                }
                else if (input[i] == ']' && stack.Count > 0)
                {
                    int start = stack.Pop();
                    int end = i;
                    string content = input.Substring(start + 1, end - start - 1);
                    segments.Add(new BracketSegment(start, end, content));
                }
            }

            // innermost first
            segments.Sort((a, b) => b.Start.CompareTo(a.Start));
            return segments;
        }

        /// <summary>
        /// Wraps a processed regex string according to the selected match style.
        public static string ApplyMatchStyle(string regexContent, string matchStyle, bool matchCase)
        {
            string wrapped;

            // Use non-capturing groups where needed (?:...) vs (...) to avoid unnecessary capture groups
            switch (matchStyle)
            {
                case "_Equals":
                    wrapped = $"^(?:{regexContent})$";
                    break;

                case "_NotEquals":
                    wrapped = $"^(?!(?:{regexContent})$).*";
                    break;

                case "_Contains":
                    wrapped = $"(?:{regexContent})";
                    break;

                case "_NotContains":
                    wrapped = $"^(?!.*(?:{regexContent})).*";
                    break;

                case "_BeginsWith":
                    wrapped = $"^(?:{regexContent})";
                    break;

                case "_NotBeginsWith":
                    wrapped = $"^(?!(?:{regexContent})).*";
                    break;

                case "_EndsWith":
                    wrapped = $"(?:{regexContent})$";
                    break;

                case "_NotEndsWith":
                    wrapped = $"^(?!.*(?:{regexContent})$).*";
                    break;

                default:
                    wrapped = $"(?:{regexContent})";
                    break;
            }

            // Apply case sensitivity inline
            if (matchCase)
            {
                return $"(?-i){wrapped}";
            }
            else
            {
                return $"(?i){wrapped}";
            }
        }
    }
}

// Push-Xaml -Files SearchText.xaml, SearchText.xaml.cs




// Rules:
// 1. Only contents inside square brackets [] are processed
// 2. Square bracketed expression [[...]]:
//   2a. Check contents -> must not contain nested brackets of any type, quantifiers
// 3. Curly bracketed expression {{...}}:
//   3a. Check contents -> must only contain digits and ONE comma
// 4. Parenthesis bracketed expression ((...)):
//   4a. Can contain nested brackets of any type. Recursively process inner brackets through parser until at inner most segments
//   4b. Treat parent as the main string (like in CompileSafeRegex now) and place 'cleaned' inner segments back into parent
//   4c. Recursively validate inner segments until all at apex
// 5. Process single-bracketed text. 
//   5a. Check contents -> must only contain accepted SafeRegex tokens: \d, \w, \s, ., +, *, ?
//   5b. Allow merging of adjacent valid tokens (ie [\d][\d+] -> \d+) but if any invalid tokens, escape entire segment
//   5c. (**Implement later**) If any invalid expressions (ie \.d or ** or etc) alert user and escape entire segment
// 6. All valid segments have outer square brackets stripped and are inserted into final regex as-is
// 7. All text outside of square brackets is escaped as literal


// Allow user to escape square brackets with \[ and \] if want literal

/////OPTIONAL/////
// Could right click sets to get common list of them, ie uppercase, lowercase, digit, not set [^abc] , etc
// could add not option to group mode 
// Should have a saftey handler for certain invalid inputs
// Could go ham and have a VS style theme where enclosed brackets at each level are assigned a color to help user see nesting
//   Further could colour any metachars so users can easily see what will be interpreted as metacharacters