package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

type Config struct {
	APIEndpoint string `mapstructure:"api_endpoint"`
	AuthToken   string `mapstructure:"auth_token"`
	DefaultRepo string `mapstructure:"default_repo"`
}

type Client struct {
	http  *http.Client
	cfg   *Config
	Token string
}

type Task struct {
	ID          string  `json:"id"`
	Title       string  `json:"title"`
	Description string  `json:"description"`
	Repository  string  `json:"repository"`
	ActionType  string  `json:"action_type"`
	Status      string  `json:"status"`
	Progress    float64 `json:"progress"`
}

type CreateTaskRequest struct {
	Title       string                 `json:"title"`
	Description string                 `json:"description"`
	Repository  string                 `json:"repository"`
	ActionType  string                 `json:"action_type"`
	Priority    string                 `json:"priority"`
	AgentConfig map[string]interface{} `json:"agent_config"`
}

func main() {
	cfg := loadConfig()
	c := &Client{http: &http.Client{Timeout: 30 * time.Second}, cfg: cfg, Token: cfg.AuthToken}

	root := &cobra.Command{Use: "autocodit", Short: "AutoCodit Agent CLI"}
	root.AddCommand(cmdCreate(c), cmdList(c), cmdGet(c), cmdCancel(c), cmdWatch(c))

	if err := root.Execute(); err != nil {
		fmt.Println("Error:", err)
		os.Exit(1)
	}
}

func loadConfig() *Config {
	viper.SetConfigName("autocodit")
	viper.SetConfigType("yaml")
	viper.AddConfigPath("$HOME/.autocodit")
	viper.AddConfigPath(".")
	viper.SetEnvPrefix("AUTOCODIT")
	viper.AutomaticEnv()
	viper.SetDefault("api_endpoint", "http://localhost:8000")

	_ = viper.ReadInConfig()
	cfg := &Config{}
	_ = viper.Unmarshal(cfg)
	return cfg
}

func (c *Client) doJSON(ctx context.Context, method, path string, in any, out any) error {
	var body io.Reader
	if in != nil {
		b, _ := json.Marshal(in)
		body = bytes.NewReader(b)
	}
	req, _ := http.NewRequestWithContext(ctx, method, c.cfg.APIEndpoint+path, body)
	req.Header.Set("Content-Type", "application/json")
	if c.Token != "" {
		req.Header.Set("Authorization", "Bearer "+c.Token)
	}
	resp, err := c.http.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		b, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("%s: %s", resp.Status, string(b))
	}
	if out != nil {
		return json.NewDecoder(resp.Body).Decode(out)
	}
	return nil
}

func cmdCreate(c *Client) *cobra.Command {
	var repo, action, priority string
	cmd := &cobra.Command{
		Use:   "create [description]",
		Short: "Create a new task",
		Args:  cobra.MinimumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			if repo == "" {
				repo = c.cfg.DefaultRepo
			}
			if repo == "" {
				return fmt.Errorf("--repo or default_repo required")
			}
			req := CreateTaskRequest{
				Title:       fmt.Sprintf("%s task", action),
				Description: args[0],
				Repository:  repo,
				ActionType:  action,
				Priority:    priority,
			}
			var task Task
			if err := c.doJSON(cmd.Context(), http.MethodPost, "/api/v1/tasks", &req, &task); err != nil {
				return err
			}
			fmt.Println("Task created:", task.ID)
			return nil
		},
	}
	cmd.Flags().StringVarP(&repo, "repo", "r", "", "owner/repo")
	cmd.Flags().StringVarP(&action, "type", "t", "plan", "plan|apply|fix|review|test|refactor|document|optimize")
	cmd.Flags().StringVarP(&priority, "priority", "p", "normal", "low|normal|high|urgent")
	return cmd
}

func cmdList(c *Client) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List tasks",
		RunE: func(cmd *cobra.Command, args []string) error {
			var resp struct{ Items []Task }
			if err := c.doJSON(cmd.Context(), http.MethodGet, "/api/v1/tasks", nil, &resp); err != nil {
				return err
			}
			for _, t := range resp.Items {
				fmt.Printf("%s %-10s %-6.1f%% %s\n", t.ID, t.Status, t.Progress*100, t.Title)
			}
			return nil
		},
	}
	return cmd
}

func cmdGet(c *Client) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "get [id]",
		Short: "Get a task",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			var t Task
			if err := c.doJSON(cmd.Context(), http.MethodGet, "/api/v1/tasks/"+args[0], nil, &t); err != nil {
				return err
			}
			out, _ := json.MarshalIndent(t, "", "  ")
			fmt.Println(string(out))
			return nil
		},
	}
	return cmd
}

func cmdCancel(c *Client) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "cancel [id]",
		Short: "Cancel a running task",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			var out map[string]any
			return c.doJSON(cmd.Context(), http.MethodPost, "/api/v1/tasks/"+args[0]+"/cancel", nil, &out)
		},
	}
	return cmd
}

func cmdWatch(c *Client) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "watch [id]",
		Short: "Watch task progress",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			id := args[0]
			for {
				var t Task
				if err := c.doJSON(cmd.Context(), http.MethodGet, "/api/v1/tasks/"+id, nil, &t); err != nil {
					return err
				}
				fmt.Printf("\r%-10s %-8s %6.1f%% %-60s", t.ID, t.Status, t.Progress*100, t.Title)
				if t.Status == "completed" || t.Status == "failed" || t.Status == "cancelled" {
					fmt.Println()
					return nil
				}
				time.Sleep(3 * time.Second)
			}
		},
	}
	return cmd
}
