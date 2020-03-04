package emptybox

import (
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestGenKey(t *testing.T) {
	key := genKey(".zshrc")
	assert.True(t, strings.HasSuffix(key, ".zshrc"))
}
