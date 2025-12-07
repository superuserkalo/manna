package main

import (
	"fmt"
	"os"

	"github.com/charmbracelet/bubbles/key"
	"github.com/charmbracelet/bubbles/help"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// keyMap defines a set of keybindings. To work for help it must satisfy
// key.Map. It could also very easily be a map[string]key.Binding.
type keyMap struct {
	Up    key.Binding
	Down  key.Binding
	Left  key.Binding
	Right key.Binding
	Help  key.Binding
	Quit  key.Binding
	Select key.Binding
}

// ShortHelp returns keybindings to be shown in the mini help view. It's part
// of the key.Map interface.
func (k keyMap) ShortHelp() []key.Binding {
	return []key.Binding{k.Help, k.Quit}
}

// FullHelp returns keybindings for the expanded help view. It's part of the
// key.Map interface.
func (k keyMap) FullHelp() [][]key.Binding {
	return [][]key.Binding{
		{k.Up, k.Down, k.Left, k.Right}, // first column
		{k.Select, k.Help, k.Quit},     // second column
	}
}

var keys = keyMap{
	Up: key.NewBinding(
		key.WithKeys("up", "k"),
		key.WithHelp("↑/k", "move up"),
	),
	Down: key.NewBinding(
		key.WithKeys("down", "j"),
		key.WithHelp("↓/j", "move down"),
	),
	Left: key.NewBinding(
		key.WithKeys("left", "h"),
		key.WithHelp("←/h", "move left"),
	),
	Right: key.NewBinding(
		key.WithKeys("right", "l"),
		key.WithHelp("→/l", "move right"),
	),
	Help: key.NewBinding(
		key.WithKeys("?"),
		key.WithHelp("?", "toggle help"),
	),
	Quit: key.NewBinding(
		key.WithKeys("q", "esc", "ctrl+c"),
		key.WithHelp("q", "quit"),
	),
	Select: key.NewBinding(
		key.WithKeys("enter", " "),
		key.WithHelp("enter", "select"),
	),
}

type model struct {
	keys       keyMap
	help       help.Model
	inputStyle lipgloss.Style
	choices  	 []string
	cursor     int
	selected   map[int]struct{}
	quitting   bool
	width      int
	votdText   string
}

func (m model) Init() tea.Cmd {
	return nil
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		// If we set a width on the help menu it can gracefully truncate
		// its view as needed.
		m.width = msg.Width
		m.help.Width = msg.Width
		m.inputStyle = m.inputStyle.Width(msg.Width)

	// Is it a key press?
	case tea.KeyMsg:

		switch {
		case key.Matches(msg, m.keys.Up):
			if m.cursor > 0 {
				m.cursor--
			}
		case key.Matches(msg, m.keys.Down):
			if m.cursor < len(m.choices)-1 {
				m.cursor++
			}
		//case key.Matches(msg, m.keys.Left):
		//case key.Matches(msg, m.keys.Right):
		case key.Matches(msg, m.keys.Help):
			m.help.ShowAll = !m.help.ShowAll
		case key.Matches(msg, m.keys.Select):
			// Handle menu selection based on current cursor.
			switch m.cursor {
			case 0: // "Verse Of The Day"
				m.votdText = PicknReturnVotd()
				m.quitting = true
				return m, tea.Quit
			default:
				// For now, keep simple toggle behavior for other menu items.
				_, ok := m.selected[m.cursor]
				if ok {
					delete(m.selected, m.cursor)
				} else {
					m.selected[m.cursor] = struct{}{}
				}
			}
		case key.Matches(msg, m.keys.Quit):
			m.quitting = true
			return m, tea.Quit
		}
	}

	// Return the updated model to the Bubble Tea runtime for processing.
	// Note that we're not returning a command.
	return m, nil
}

func (m model) View() string {
	if m.quitting {
		goodbye := GoodbyeMessage()
		return goodbye + "\n"
	}

	// The header
	s := "Manna\n\n"

	// Iterate over our choices
	for i, choice := range m.choices {

		// Is the cursor pointing at this choice?
		cursor := " " // no cursor
		if m.cursor == i {
			cursor = ">" // cursor!
		}

		// Is this choice selected?
		checked := " " // not selected
		if _, ok := m.selected[i]; ok {
			checked = "x" // selected!
		}

		// Render the row
		s += fmt.Sprintf("%s [%s] %s\n", cursor, checked, choice)
	}

	helpView := m.help.View(m.keys)
	s += "\n" + m.inputStyle.Render(helpView)
	//height := 8 - strings.Count(status, "\n") - strings.Count(helpView, "\n")

	// The footer
	//s += "\nUse ↑/↓ to move, Enter to select, q to quit.\n"

	// Send the UI for rendering
	return s
}

func initialModel() model {
	// Configure the help view styles so that all text uses a bright
	// foreground color and the same background as the container.
	helpModel := help.New()
	//bg := lipgloss.Color("12")
	fg := lipgloss.Color("#ffffff")

	helpModel.Styles.ShortKey = helpModel.Styles.ShortKey.
		Foreground(fg)
		//Background(bg)
	helpModel.Styles.ShortDesc = helpModel.Styles.ShortDesc.
		Foreground(fg)
		//Background(bg)
	helpModel.Styles.FullKey = helpModel.Styles.FullKey.
		Foreground(fg)
		//Background(bg)
	helpModel.Styles.FullDesc = helpModel.Styles.FullDesc.
		Foreground(fg)
		//Background(bg)

	return model{
		keys: keys,
		help: helpModel,
		inputStyle: lipgloss.NewStyle().
			Bold(true).
		//	Background(bg).
			Foreground(fg),
		// Our to-do list is a grocery list
		choices: []string{
			"Verse Of The Day",
			"Lookup Books/Chapters/Verses",
			"Set VOTD or specific verse on shell startup",
		},
		// A map which indicates which choices are selected. We're using
		// the  map like a mathematical set. The keys refer to the indexes
		// of the `choices` slice, above.
		selected: make(map[int]struct{}),
		quitting: false,
		votdText: "",
	}
}

func main() {
	p := tea.NewProgram(initialModel())
	m, err := p.Run()
	if err != nil {
		fmt.Printf("Alas, there's been an error: %v", err)
		os.Exit(1)
	}

	// After the TUI exits, print any verse-of-the-day text the
	// user requested to standard output.
	if final, ok := m.(model); ok {
		if final.votdText != "" {
			fmt.Println()
			fmt.Println(final.votdText)
		}
	}
}
