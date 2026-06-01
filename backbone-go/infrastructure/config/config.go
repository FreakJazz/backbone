// Package config provides configuration management
package config

import (
	"fmt"
	"os"
	"time"

	"github.com/spf13/viper"
)

// Config represents application configuration
type Config struct {
	// Application
	AppName     string `mapstructure:"app_name"`
	AppVersion  string `mapstructure:"app_version"`
	Environment string `mapstructure:"environment"`
	Debug       bool   `mapstructure:"debug"`

	// Server
	ServerHost string `mapstructure:"server_host"`
	ServerPort int    `mapstructure:"server_port"`

	// Database
	DatabaseURL      string        `mapstructure:"database_url"`
	DatabaseMaxConns int           `mapstructure:"database_max_conns"`
	DatabaseTimeout  time.Duration `mapstructure:"database_timeout"`

	// Logging
	LogLevel  string `mapstructure:"log_level"`
	LogFormat string `mapstructure:"log_format"`

	// Event Bus
	EventBusType  string   `mapstructure:"event_bus_type"` // kafka, redis, rabbitmq, inmemory
	KafkaBrokers  []string `mapstructure:"kafka_brokers"`
	RedisAddr     string   `mapstructure:"redis_addr"`
	RedisPassword string   `mapstructure:"redis_password"`
	RedisDB       int      `mapstructure:"redis_db"`
	RabbitMQURL   string   `mapstructure:"rabbitmq_url"`

	// Event Store
	EventStorePath string `mapstructure:"event_store_path"`
}

// LoadConfig loads configuration from file and environment variables
func LoadConfig(configPath string) (*Config, error) {
	viper.SetConfigName("config")
	viper.SetConfigType("yaml")
	viper.AddConfigPath(configPath)
	viper.AddConfigPath(".")
	viper.AddConfigPath("./config")

	// Set defaults
	setDefaults()

	// Read config file
	if err := viper.ReadInConfig(); err != nil {
		if _, ok := err.(viper.ConfigFileNotFoundError); !ok {
			return nil, fmt.Errorf("failed to read config file: %w", err)
		}
	}

	// Override with environment variables
	viper.AutomaticEnv()

	var config Config
	if err := viper.Unmarshal(&config); err != nil {
		return nil, fmt.Errorf("failed to unmarshal config: %w", err)
	}

	return &config, nil
}

// setDefaults sets default configuration values
func setDefaults() {
	viper.SetDefault("app_name", "backbone-app")
	viper.SetDefault("app_version", "1.0.0")
	viper.SetDefault("environment", "development")
	viper.SetDefault("debug", false)

	viper.SetDefault("server_host", "0.0.0.0")
	viper.SetDefault("server_port", 8000)

	viper.SetDefault("database_max_conns", 10)
	viper.SetDefault("database_timeout", 30*time.Second)

	viper.SetDefault("log_level", "info")
	viper.SetDefault("log_format", "json")

	viper.SetDefault("event_bus_type", "inmemory")
	viper.SetDefault("kafka_brokers", []string{"localhost:9092"})
	viper.SetDefault("redis_addr", "localhost:6379")
	viper.SetDefault("redis_password", "")
	viper.SetDefault("redis_db", 0)
	viper.SetDefault("rabbitmq_url", "amqp://guest:guest@localhost:5672/")

	viper.SetDefault("event_store_path", "./event_store")
}

// GetEnv gets an environment variable with a default value
func GetEnv(key, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return value
}

// IsProduction checks if the environment is production
func (c *Config) IsProduction() bool {
	return c.Environment == "production"
}

// IsDevelopment checks if the environment is development
func (c *Config) IsDevelopment() bool {
	return c.Environment == "development"
}

// IsStaging checks if the environment is staging
func (c *Config) IsStaging() bool {
	return c.Environment == "staging"
}
